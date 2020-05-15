import base64
import inspect
import json
import logging
import warnings
from collections import defaultdict, namedtuple
from enum import Enum, EnumMeta
from types import FunctionType
from typing import Union, get_type_hints

from decouple import config

from lpipe import kinesis, sentry, sqs
from lpipe.exceptions import (
    FailButContinue,
    FailCatastrophically,
    InvalidConfigurationError,
    InvalidPathError,
    InvalidPayloadError,
    LpipeBaseException,
)
from lpipe.logging import ServerlessLogger
from lpipe.utils import AutoEncoder, _repr, exception_to_str, get_enum_value, get_nested


class QueueType(Enum):
    RAW = 1
    KINESIS = 2
    SQS = 3


class Queue:
    """Represents a queue path in an Action.

    Note:
        Kinesis uses name.
        SQS uses name or url.

    Args:
        type (QueueType)
        path (str): Value of the "path" field set on the message we'll send to this queue.
        name (str, optional): Queue name
        url (str, optional): Queue URL/URI

    Attributes:
        type (QueueType)
        path (str)
        name (str)
        url (str)

    """

    def __init__(self, type, path, name=None, url=None):
        assert name or url
        assert isinstance(type, QueueType)
        self.type = type
        self.path = path
        self.name = name
        self.url = url

    def __repr__(self):
        return _repr(self, ["type", "name", "url"])


def clean_path(path_enum: EnumMeta, path):
    if isinstance(path, Queue):
        return path
    else:
        try:
            return get_enum_value(path_enum, path)
        except Exception as e:
            raise InvalidPathError(
                "Unable to cast your path identifier to an enum."
            ) from e


class Action:
    def __init__(
        self, functions=[], paths=[], required_params=None, include_all_params=False
    ):
        assert functions or paths
        self.functions = functions
        self.paths = paths
        self.required_params = required_params
        self.include_all_params = include_all_params

    def __repr__(self):
        return _repr(self, ["functions", "paths"])

    def copy(self):
        return type(self)(
            functions=self.functions,
            paths=[
                p if isinstance(p, Queue) else str(p).split(".")[-1] for p in self.paths
            ],
            required_params=self.required_params,
        )


class Payload:
    def __init__(self, path, kwargs: dict, event_source=None):
        self.path = path
        self.kwargs = kwargs
        self.event_source = event_source

    def validate(self, path_enum: EnumMeta = None):
        if path_enum:
            assert isinstance(
                clean_path(path_enum, self.path), path_enum
            ) or isinstance(self.path, Queue)
        else:
            assert isinstance(self.path, Queue)
        return self

    def to_dict(self) -> dict:
        return {"path": self.path, "kwargs": self.kwargs}

    def __repr__(self):
        return _repr(self, ["path", "kwargs"])


def build_response(n_records, n_ok, logger) -> dict:
    response = {
        "event": "Finished.",
        "stats": {"received": n_records, "successes": n_ok},
    }
    if hasattr(logger, "events") and logger.events:
        response["logs"] = json.dumps(logger.events, cls=AutoEncoder)
    return response


def process_event(
    event,
    context,
    paths: dict,
    queue_type: QueueType,
    path_enum: EnumMeta = None,
    default_path=None,
    logger=None,
    debug=False,
):
    """Process an AWS Lambda event.

    Args:
        event: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
        context: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
        paths (dict): Keys are path names / enums and values are a list of Action objects
        queue_type (QueueType): The event source type.
        path_enum (EnumMeta): An Enum class which define the possible paths available in this lambda.
        default_path: A string or Enum which will be run for every message received.
        logger:
        debug (bool):
    """
    try:
        if not logger:
            logger = ServerlessLogger(
                level=logging.DEBUG if debug else logging.INFO,
                process=getattr(
                    context, "function_name", config("FUNCTION_NAME", default=None)
                ),
            )

        if debug and isinstance(logger, ServerlessLogger):
            logger.persist = True
    except Exception as e:
        raise InvalidConfigurationError("Failed to initialize logger.") from e

    logger.debug(f"Event received. queue: {queue_type}, event: {event}")
    try:
        assert isinstance(queue_type, QueueType)
    except AssertionError as e:
        raise InvalidConfigurationError(f"Invalid queue type '{queue_type}'") from e

    if not path_enum:
        try:
            path_enum = Enum("AutoPath", [k.upper() for k in paths.keys()])
            paths = {clean_path(path_enum, k): v for k, v in paths.items()}
        except KeyError as e:
            raise InvalidConfigurationError from e

    successful_records = []
    records = get_records_from_event(queue_type, event)
    try:
        assert isinstance(records, list)
    except AssertionError as e:
        logger.error(f"'records' is not a list {exception_to_str(e)}")
        return build_response(0, 0, logger)

    output = []
    exceptions = []
    for encoded_record in records:
        ret = None
        try:
            try:
                _payload = get_payload_from_record(
                    queue_type=queue_type,
                    record=encoded_record,
                    validate=False if default_path else True,
                )
                _path = default_path if default_path else _payload["path"]
                _kwargs = _payload if default_path else _payload["kwargs"]
                _event_source = get_event_source(queue_type, encoded_record)
                payload = Payload(_path, _kwargs, _event_source).validate(path_enum)
            except AssertionError as e:
                raise InvalidPayloadError(
                    "'path' or 'kwargs' missing from payload."
                ) from e
            except TypeError as e:
                raise InvalidPayloadError(
                    f"Bad record provided for queue type {queue_type}. {encoded_record} {exception_to_str(e)}"
                ) from e

            with logger.context(bind={"payload": payload.to_dict()}):
                logger.log(f"Record received.")

            # Run your path/action/functions against the payload found in this record.
            ret = execute_payload(
                payload=payload,
                path_enum=path_enum,
                paths=paths,
                logger=logger,
                event=event,
                context=context,
                debug=debug,
            )

            # Will handle any cleanup necessary for a successful record later.
            successful_records.append(encoded_record)
        except FailButContinue as e:
            # CAPTURES:
            #    InvalidPayloadError
            #    InvalidPathError
            logger.error(str(e))
            sentry.capture(e)
            continue  # User can say "bad thing happened but keep going." This drops poisoned records on the floor.
        except FailCatastrophically as e:
            # CAPTURES:
            #    InvalidConfigurationError
            # raise (later)
            exceptions.append({"exception": e, "record": encoded_record})
        output.append(ret)

    response = build_response(
        n_records=len(records), n_ok=len(successful_records), logger=logger
    )

    if exceptions:
        # Handle any cleanup necessary for successful records before creating an error state.
        advanced_cleanup(queue_type, successful_records, logger)

        logger.info(
            f"Encountered exceptions while handling one or more records. RESPONSE: {response}"
        )
        raise FailCatastrophically(exceptions)

    if any(output):
        response["output"] = output
    if debug:
        response["debug"] = json.dumps({"records": records}, cls=AutoEncoder)
    return response


def execute_payload(
    payload: Payload,
    path_enum: EnumMeta,
    paths: dict,
    logger,
    event,
    context,
    debug=False,
):
    """Execute functions, paths, and shortcuts in a Path.

    Args:
        payload (Payload):
        path_enum (EnumMeta): An Enum class which define the possible paths available in this lambda.
        paths (dict): Keys are path names / enums and values are a list of Action objects
        logger:
        event: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
        context: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
    """
    if not logger:
        logger = ServerlessLogger()

    ret = None

    if not isinstance(payload.path, path_enum):
        payload.path = clean_path(path_enum, payload.path)

    if isinstance(payload.path, Enum):  # PATH
        # Allow someone to simplify their definition of a Path to a list of functions.
        if all([isinstance(f, FunctionType) for f in paths[payload.path]]):
            paths[payload.path] = [Action(functions=action)]

        for action in paths[payload.path]:
            assert isinstance(action, Action)

            # Build action kwargs and validate type hints
            try:
                dummy = ["logger", "event"]
                action_kwargs = build_action_kwargs(
                    action, {**{k: None for k in dummy}, **payload.kwargs}
                )
                for k in dummy:
                    action_kwargs.pop(k, None)
            except (TypeError, AssertionError) as e:
                raise InvalidPayloadError(
                    f"Failed to run {payload.path.name} {action} due to {exception_to_str(e)}"
                ) from e

            # Run action functions
            for f in action.functions:
                assert isinstance(f, FunctionType)
                try:
                    # TODO: if ret, set _last_output
                    _log_context = {"path": payload.path.name, "function": f.__name__}
                    with logger.context(bind={**_log_context, "kwargs": action_kwargs}):
                        logger.log("Executing function.")
                    with logger.context(bind=_log_context):
                        ret = f(
                            **{
                                **action_kwargs,
                                "logger": logger,
                                "event": {
                                    "event": event,
                                    "context": context,
                                    "payload": payload,
                                },
                            }
                        )

                    if ret:
                        _payloads = []
                        try:
                            if isinstance(ret, Payload):
                                _payloads.append(ret.validate(path_enum))
                            elif isinstance(ret, list):
                                for r in ret:
                                    if isinstance(r, Payload):
                                        _payloads.append(r.validate(path_enum))
                        except Exception as e:
                            logger.debug(exception_to_str(e))
                            raise FailButContinue(
                                f"Something went wrong while extracting Payloads from a function return value. {ret}"
                            ) from e

                        for p in _payloads:
                            logger.debug(f"Function returned a Payload. Executing. {p}")
                            try:
                                ret = execute_payload(
                                    p, path_enum, paths, logger, event, context, debug
                                )
                            except Exception as e:
                                logger.debug(exception_to_str(e))
                                raise FailButContinue(
                                    f"Failed to execute returned Payload. {p}"
                                ) from e
                except LpipeBaseException:
                    # CAPTURES:
                    #    FailButContinue
                    #    FailCatastrophically
                    raise
                except Exception as e:
                    logger.error(
                        f"Skipped {payload.path.name} {f.__name__} due to unhandled Exception. This is very serious; please update your function to handle this. Reason: {exception_to_str(e)}"
                    )
                    sentry.capture(e)
                    if debug:
                        raise FailCatastrophically() from e

            # Run action paths / shortcuts
            for path_descriptor in action.paths:
                _payload = Payload(
                    clean_path(path_enum, path_descriptor),
                    action_kwargs,
                    payload.event_source,
                ).validate(path_enum)
                ret = execute_payload(
                    _payload, path_enum, paths, logger, event, context, debug
                )
    elif isinstance(payload.path, Queue):  # SHORTCUT
        queue = payload.path
        assert isinstance(queue.type, QueueType)
        with logger.context(
            bind={
                "path": queue.path,
                "queue_type": queue.type,
                "queue_name": queue.name,
                "kwargs": payload.kwargs,
            }
        ):
            logger.log("Pushing record.")
        put_record(queue=queue, record={"path": queue.path, "kwargs": payload.kwargs})
    else:
        logger.info(
            f"Path should be a string (path name), Path (path Enum), or Queue: {payload.path})"
        )

    return ret


def advanced_cleanup(queue_type, records, logger, **kwargs):
    """If exceptions were raised, cleanup all successful records before raising.

    Args:
        queue_type (QueueType):
        records (list): records which we succesfully executed
        logger:
    """
    if queue_type == QueueType.SQS:
        cleanup_sqs_records(records, logger)
    # If the queue type was not handled, no cleanup was necessary by lpipe.


def cleanup_sqs_records(records, logger):
    base_err_msg = (
        "Unable to delete successful records messages from SQS queue. AWS should "
        "still handle this automatically when the lambda finishes executing, but "
        "this may result in successful messages being sent to the DLQ if any "
        "other messages fail."
    )
    try:
        Message = namedtuple("Message", ["message_id", "receipt_handle"])
        messages = defaultdict(list)
        for record in records:
            m = Message(
                message_id=get_nested(record, ["messageId"]),
                receipt_handle=get_nested(record, ["receiptHandle"]),
            )
            messages[get_nested(record, ["eventSourceARN"])].append(m)
        for k in messages.keys():
            queue_url = sqs.get_queue_url(k)
            sqs.batch_delete_messages(
                queue_url,
                [
                    {"Id": m.message_id, "ReceiptHandle": m.receipt_handle}
                    for m in messages
                ],
            )
    except KeyError as e:
        logger.warning(
            f"{base_err_msg} If you're testing, this is not an issue. {exception_to_str(e)}"
        )
    except Exception as e:
        logger.warning(f"{base_err_msg} {exception_to_str(e)}")


def build_action_kwargs(action: Action, kwargs: dict) -> dict:
    """Build dictionary of kwargs for a specific action.

    Args:
        action (Action)
        kargs (dict): kwargs provided in the event's message

    Returns:
        dict: validated kwargs required by action
    """
    action_kwargs = build_kwargs(
        functions=action.functions,
        required_params=action.required_params,
        kwargs=kwargs,
    )
    if action.include_all_params:
        action_kwargs.update(kwargs)
    return action_kwargs


def build_kwargs(kwargs: dict, functions: list, required_params: list = None) -> dict:
    """Build dictionary of kwargs for the union of function signatures.

    Args:
        functions (list): functions which a particular action should call
        required_params (list): manually defined parameters
        kargs (dict): kwargs provided in the event's message

    Returns:
        dict: validated kwargs required by action
    """
    kwargs_union = {}
    if not required_params and functions:
        kwargs_union = validate_signature(functions, kwargs)
    elif required_params and isinstance(required_params, list):
        for param in required_params:
            param_name = param[0] if isinstance(param, tuple) else param
            try:
                # Assert required field was provided.
                assert param_name in kwargs
            except AssertionError as e:
                raise InvalidPayloadError(f"Missing param '{param_name}'") from e

            # Set param in kwargs. If the param is a tuple, use the [1] as the new key.
            if isinstance(param, tuple) and len(param) == 2:
                kwargs_union[param[1]] = kwargs[param[0]]
            else:
                kwargs_union[param] = kwargs[param]
    elif not required_params:
        return {}
    else:
        raise InvalidPayloadError(
            "You either didn't provide functions or required_params was not an instance of list or NoneType."
        )
    return kwargs_union


def _merge(functions: list, iter):
    """Get a set of attributes describing several functions.

    Args:
        functions (list): list of functions (FunctionType)

    Raises:
        TypeError: If two functions have the same parameter name with different types or defaults.
    """
    output = {}
    for f in functions:
        assert isinstance(f, FunctionType)
        i = iter(f)
        for k, v in i.items():
            if k in output:
                try:
                    assert v == output[k]
                except AssertionError as e:
                    raise TypeError(
                        f"Incompatible functions {functions}: {k} represented as both {v} and {output[k]}"
                    ) from e
            else:
                output[k] = v
    return output


def _merge_signatures(functions: list):
    """Create a combined list of function parameters."""
    return _merge(functions, lambda f: inspect.signature(f).parameters)


def _merge_type_hints(functions: list):
    """Create a combined list of function parameter type hints."""
    return _merge(functions, lambda f: get_type_hints(f))


def _get_defaults(signature):
    """Create a dict of function parameters with defaults."""
    return {
        k: v.default
        for k, v in signature.items()
        if v.default is not inspect.Parameter.empty
    }


def validate_signature(functions: list, params: dict) -> dict:
    """Validate and build kwargs for a set of functions based on their signatures.

    Args:
        functions (list): functions
        params (dict): kwargs provided in the event's message

    Returns:
        dict: validated kwargs required by the provided set of functions
    """
    signature = _merge_signatures(functions)
    defaults = _get_defaults(signature)
    hints = _merge_type_hints(functions)

    validated = {}
    for k, v in signature.items():
        if k in params:
            p = params[k]
            if k in hints:
                t = hints[k]
                try:
                    if hasattr(t, "__origin__") and t.__origin__ is Union:
                        # https://stackoverflow.com/a/49471187
                        assert any([isinstance(p, typ) for typ in t.__args__])
                    else:
                        assert isinstance(p, t)
                except AssertionError as e:
                    raise TypeError(f"Type of {k} should be {t} not {type(p)}.") from e
                validated[k] = p
            else:
                validated[k] = p
        elif k not in ("kwargs", "args"):
            try:
                assert k in defaults
            except AssertionError as e:
                raise TypeError(f"{functions} missing required argument: '{k}'") from e

    return validated


def get_raw_payload(record) -> dict:
    """Decode and validate a json record."""
    assert record is not None
    return record if isinstance(record, dict) else json.loads(record)


def get_kinesis_payload(record) -> dict:
    """Decode and validate a kinesis record."""
    assert record["kinesis"]["data"] is not None
    return json.loads(base64.b64decode(bytearray(record["kinesis"]["data"], "utf-8")))


def get_sqs_payload(record) -> dict:
    """Decode and validate an sqs record."""
    assert record["body"] is not None
    return json.loads(record["body"])


def get_records_from_event(queue_type: QueueType, event):
    if queue_type == QueueType.RAW:
        return event
    if queue_type == QueueType.KINESIS:
        return event["Records"]
    if queue_type == QueueType.SQS:
        return event["Records"]


def get_event_source(queue_type: QueueType, record):
    if queue_type in (QueueType.RAW, QueueType.KINESIS, QueueType.SQS):
        return get_nested(record, ["event_source_arn"], None)
    warnings.warn(f"Unable to fetch event_source for {queue_type} record.")
    return None


def get_payload_from_record(queue_type: QueueType, record, validate=True) -> dict:
    try:
        if queue_type == QueueType.RAW:
            payload = get_raw_payload(record)
        if queue_type == QueueType.KINESIS:
            payload = get_kinesis_payload(record)
        if queue_type == QueueType.SQS:
            payload = get_sqs_payload(record)
    except json.JSONDecodeError as e:
        raise InvalidPayloadError(
            f"Payload contained invalid json. {exception_to_str(e)}"
        ) from e
    if validate:
        for field in ["path", "kwargs"]:
            assert field in payload
    return payload


def put_record(queue: Queue, record: dict):
    if queue.type == QueueType.KINESIS:
        return kinesis.put_record(stream_name=queue.name, data=record)
    if queue.type == QueueType.SQS:
        if not queue.url:
            queue.url = sqs.get_queue_url(queue.name)
        try:
            return sqs.put_message(queue_url=queue.url, data=record)
        except Exception as e:
            raise FailCatastrophically(f"Failed to send message to {queue}") from e
