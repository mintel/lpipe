import base64
import json
import warnings
from collections import defaultdict, namedtuple
from enum import Enum, EnumMeta
from types import FunctionType
from typing import Any, NamedTuple, Union

import lpipe.exceptions
import lpipe.logging
from lpipe import normalize, signature, utils
from lpipe.action import Action
from lpipe.contrib import kinesis, mindictive, sqs
from lpipe.payload import Payload
from lpipe.queue import Queue, QueueType

RESERVED_KEYWORDS = set(["logger", "state", "payload"])


class State(NamedTuple):
    """Represents the state of the call to process_event.

    Args:
        event (Any): https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
        context (Any): https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
        paths (dict): Keys are path names / enums and values are a list of Action objects
        path_enum (EnumMeta): An Enum class which define the possible paths available in this lambda.
        logger:
        exception_handler (FunctionType): A function which will be used to capture exceptions (e.g. contrib.sentry.capture)
        debug (bool):
    """

    event: Any
    context: Any
    paths: dict
    path_enum: EnumMeta
    logger: Any
    debug: bool = False
    exception_handler: FunctionType = None


def build_event_response(n_records, n_ok, logger) -> dict:
    response = {
        "event": "Finished.",
        "stats": {"received": n_records, "successes": n_ok},
    }
    if hasattr(logger, "events") and logger.events:
        response["logs"] = json.dumps(logger.events, cls=utils.AutoEncoder)
    return response


def log_exception(state: State, e: BaseException):
    state.logger.error(utils.exception_to_str(e))
    if state.exception_handler:
        state.exception_handler(e)


def process_event(
    event: Any,
    context: Any,
    queue_type: QueueType,
    paths: dict = None,
    path_enum: EnumMeta = None,
    default_path: Union[str, Enum] = None,
    call: FunctionType = None,
    logger: Any = None,
    debug: bool = False,
    exception_handler: FunctionType = None,
) -> dict:
    """Process an AWS Lambda event.

    Args:
        event: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
        context: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
        queue_type (QueueType): The event source type.
        paths (dict): Keys are path names / enums and values are a list of Action objects
        path_enum (EnumMeta): An Enum class which define the possible paths available in this lambda.
        default_path (Union[str, Enum]): The path to be run for every message received.
        call (FunctionType): A callable which, if set and `paths` is not, will disable directed-graph workflow features and default to calling this
        logger:
        debug (bool):
        exception_handler (FunctionType): A function which will be used to capture exceptions (e.g. contrib.sentry.capture)
    """
    logger = lpipe.logging.setup(logger=logger, context=context, debug=debug)
    logger.debug(f"Event received. queue: {queue_type}, event: {event}")

    try:
        assert isinstance(queue_type, QueueType)
    except AssertionError as e:
        raise lpipe.exceptions.InvalidConfigurationError(
            f"Invalid queue type '{queue_type}'"
        ) from e

    if isinstance(call, FunctionType):
        if not paths:
            default_path = "AUTO_PATH"
            paths = {default_path: [call]}
        else:
            raise lpipe.exceptions.InvalidConfigurationError(
                "If you initialize lpipe with a function/callable, you cannot define paths, as you have disabled the directed-graph interface."
            )

    paths, path_enum = normalize.normalize_path_enum(path_enum=path_enum, paths=paths)
    state = State(
        event=event,
        context=context,
        logger=logger,
        debug=debug,
        paths=paths,
        path_enum=path_enum,
        exception_handler=exception_handler,
    )

    successful_records = []
    records = get_records_from_event(queue_type, state.event)
    try:
        assert isinstance(records, list)
    except AssertionError as e:
        state.logger.error(f"'records' is not a list {utils.exception_to_str(e)}")
        return build_event_response(0, 0, state.logger)

    _output = []
    _exceptions = []
    for encoded_record in records:
        ret = None
        try:
            try:
                decoded_record = get_payload_from_record(
                    queue_type=queue_type,
                    record=encoded_record,
                    validate=False if default_path else True,
                )
                payload = Payload(
                    path=default_path if default_path else decoded_record["path"],
                    kwargs=decoded_record if default_path else decoded_record["kwargs"],
                    event_source=get_event_source(queue_type, encoded_record),
                ).validate(state.path_enum)
            except AssertionError as e:
                raise lpipe.exceptions.InvalidPayloadError(
                    "'path' or 'kwargs' missing from payload."
                ) from e
            except TypeError as e:
                raise lpipe.exceptions.InvalidPayloadError(
                    f"Bad record provided for queue type {queue_type}. {encoded_record} {utils.exception_to_str(e)}"
                ) from e

            with state.logger.context(bind={"payload": payload.to_dict()}):
                state.logger.log("Record received.")

            # Run your path/action/functions against the payload found in this record.
            ret = execute_payload(payload=payload, state=state)

            # Will handle cleanup for successful records later, if necessary.
            successful_records.append(encoded_record)
        except lpipe.exceptions.FailButContinue as e:
            # CAPTURES:
            #    lpipe.exceptions.InvalidPayloadError
            #    lpipe.exceptions.InvalidPathError
            log_exception(state, e)
            continue  # User can say "bad thing happened but keep going." This drops poisoned records on the floor.
        except lpipe.exceptions.FailCatastrophically as e:
            # CAPTURES:
            #    lpipe.exceptions.InvalidConfigurationError
            # raise (later)
            log_exception(state, e)
            _exceptions.append({"exception": e, "record": encoded_record})
        _output.append(ret)

    response = build_event_response(
        n_records=len(records), n_ok=len(successful_records), logger=state.logger
    )

    if _exceptions:
        # Handle cleanup for successful records, if necessary, before creating an error state.
        advanced_cleanup(queue_type, successful_records, state.logger)
        raise lpipe.exceptions.FailCatastrophically(
            f"Encountered catastrophic exceptions while handling one or more records: {response}"
        )

    if any(_output):
        response["output"] = _output
    if state.debug:
        response["debug"] = json.dumps({"records": records}, cls=utils.AutoEncoder)

    return response


def execute_payload(payload: Payload, state: State) -> Any:
    """Given a Payload, execute Actions in a Path and fire off messages to the payload's Queues.

    Args:
        payload (Payload):
        state (State):
    """
    ret = None

    if payload.path is not None and not isinstance(payload.path, state.path_enum):
        payload.path = normalize.normalize_path(state.path_enum, payload.path)

    if isinstance(payload.path, Enum):  # PATH
        state.paths[payload.path] = normalize.normalize_actions(
            state.paths[payload.path]
        )

        for action in state.paths[payload.path]:
            ret = execute_action(payload=payload, action=action, state=state)

    elif isinstance(payload.queue, Queue):  # QUEUE (aka SHORTCUT)
        queue = payload.queue
        assert isinstance(queue.type, QueueType)
        if queue.path:
            record = {"path": queue.path, "kwargs": payload.kwargs}
        else:
            record = payload.kwargs
        with state.logger.context(
            bind={
                "path": queue.path,
                "queue_type": queue.type,
                "queue_name": queue.name,
                "record": record,
            }
        ):
            state.logger.log("Pushing record.")
        put_record(queue=queue, record=record)
    else:
        state.logger.info(
            f"Path should be a string (path name), Path (path Enum), or Queue: {payload.path})"
        )

    return ret


def execute_action(payload: Payload, action: Action, state: State) -> Any:
    """Execute functions, paths, and queues (shortcuts) in an Action.

    Args:
        payload (Payload):
        action: (Action):
        state (State):
    """
    assert isinstance(action, Action)
    ret = None

    # Build action kwargs and validate type hints
    try:
        if RESERVED_KEYWORDS & set(payload.kwargs):
            state.logger.warning(
                f"Payload contains a reserved argument name. Please update your function use a different argument name. Reserved keywords: {RESERVED_KEYWORDS}"
            )
        action_kwargs = build_action_kwargs(
            action, {**{k: None for k in RESERVED_KEYWORDS}, **payload.kwargs}
        )
        for k in RESERVED_KEYWORDS:
            action_kwargs.pop(k, None)
    except (TypeError, AssertionError) as e:
        raise lpipe.exceptions.InvalidPayloadError(
            f"Failed to run {payload.path.name} {action} due to {utils.exception_to_str(e)}"
        ) from e

    default_kwargs = {"logger": state.logger, "state": state, "payload": payload}

    # Run action functions
    for f in action.functions:
        assert isinstance(f, FunctionType)
        try:
            # TODO: if ret, evaluate viability of passing to next in sequence
            _log_context = {"path": payload.path.name, "function": f.__name__}
            with state.logger.context(bind={**_log_context, "kwargs": action_kwargs}):
                state.logger.log("Executing function.")
            with state.logger.context(bind=_log_context):
                ret = f(**{**action_kwargs, **default_kwargs})
            ret = return_handler(ret=ret, state=state)
        except lpipe.exceptions.LPBaseException:
            # CAPTURES:
            #    lpipe.exceptions.FailButContinue
            #    lpipe.exceptions.FailCatastrophically
            raise
        except Exception as e:
            state.logger.error(
                f"Skipped {payload.path.name} {f.__name__} due to unhandled Exception {e.__class__.__name__}. This is very serious; please update your function to handle this."
            )
            log_exception(state, e)
            if state.debug:
                raise lpipe.exceptions.FailCatastrophically() from e

    payloads = []
    for _path in action.paths:
        payloads.append(
            Payload(
                path=normalize.normalize_path(state.path_enum, _path),
                kwargs=action_kwargs,
                event_source=payload.event_source,
            ).validate(state.path_enum)
        )

    for _queue in action.queues:
        payloads.append(
            Payload(
                queue=_queue, kwargs=action_kwargs, event_source=payload.event_source
            ).validate()
        )

    for p in payloads:
        ret = execute_payload(payload=p, state=state)

    return ret


def return_handler(ret: Any, state: State) -> Any:
    if not ret:
        return ret
    _payloads = []
    try:
        if isinstance(ret, Payload):
            _payloads.append(ret.validate(state.path_enum))
        elif isinstance(ret, list):
            for r in ret:
                if isinstance(r, Payload):
                    _payloads.append(r.validate(state.path_enum))
    except Exception as e:
        state.logger.debug(utils.exception_to_str(e))
        raise lpipe.exceptions.FailButContinue(
            f"Something went wrong while extracting Payloads from a function return value: {ret}"
        ) from e

    if _payloads:
        state.logger.debug(f"{len(_payloads)} dynamic payloads received")
    for p in _payloads:
        state.logger.debug(f"executing dynamic payload: {p}")
        try:
            ret = execute_payload(payload=p, state=state)
        except Exception as e:
            state.logger.debug(utils.exception_to_str(e))
            raise lpipe.exceptions.FailButContinue(
                f"Failed to execute returned Payload: {p}"
            ) from e
    return ret


def advanced_cleanup(queue_type: QueueType, records: list, logger, **kwargs):
    """If exceptions were raised, cleanup all successful records before raising.

    Args:
        queue_type (QueueType):
        records (list): records which we succesfully executed
        logger:
    """
    if queue_type == QueueType.SQS:
        cleanup_sqs_records(records, logger)
    # If the queue type was not handled, no cleanup was necessary by lpipe.


def cleanup_sqs_records(records: list, logger):
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
                message_id=mindictive.get_nested(record, ["messageId"]),
                receipt_handle=mindictive.get_nested(record, ["receiptHandle"]),
            )
            messages[mindictive.get_nested(record, ["eventSourceARN"])].append(m)
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
            f"{base_err_msg} If you're testing, this is not an issue. {utils.exception_to_str(e)}"
        )
    except Exception as e:
        logger.warning(f"{base_err_msg} {utils.exception_to_str(e)}")


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
        kwargs_union = signature.validate(functions, kwargs)
    elif required_params and isinstance(required_params, list):
        for param in required_params:
            param_name = param[0] if isinstance(param, tuple) else param
            try:
                # Assert required field was provided.
                assert param_name in kwargs
            except AssertionError as e:
                raise lpipe.exceptions.InvalidPayloadError(
                    f"Missing param '{param_name}'"
                ) from e

            # Set param in kwargs. If the param is a tuple, use the [1] as the new key.
            if isinstance(param, tuple) and len(param) == 2:
                kwargs_union[param[1]] = kwargs[param[0]]
            else:
                kwargs_union[param] = kwargs[param]
    elif not required_params:
        return {}
    else:
        raise lpipe.exceptions.InvalidPayloadError(
            "You either didn't provide functions or required_params was not an instance of list or NoneType."
        )
    return kwargs_union


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
        return mindictive.get_nested(record, ["event_source_arn"], None)
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
        raise lpipe.exceptions.InvalidPayloadError(
            f"Payload contained invalid json. {utils.exception_to_str(e)}"
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
            raise lpipe.exceptions.FailCatastrophically(
                f"Failed to send message to {queue}"
            ) from e
