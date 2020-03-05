import base64
import importlib
import inspect
import json
import logging
import shlex
import warnings
from collections import namedtuple
from enum import Enum, EnumMeta
from types import FunctionType
from typing import Callable, Union, get_type_hints

import requests
from decouple import config

from lpipe import kinesis, sentry, sqs
from lpipe.exceptions import (
    FailButContinue,
    FailCatastrophically,
    GraphQLError,
    InvalidInputError,
    InvalidPathError,
)
from lpipe.logging import ServerlessLogger
from lpipe.utils import AutoEncoder, _repr, batch, get_enum_value, get_nested


class Action:
    def __init__(self, functions=[], paths=[], required_params=None):
        assert functions or paths
        self.functions = functions
        self.paths = paths
        self.required_params = required_params

    def __repr__(self):
        return _repr(self, ["functions", "paths"])


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


class Payload:
    def __init__(self, path, kwargs: dict):
        self.path = path
        self.kwargs = kwargs

    def validate(self, path_enum: EnumMeta = None):
        if path_enum:
            assert isinstance(
                get_enum_value(path_enum, self.path), path_enum
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
    path_enum: EnumMeta,
    paths: dict,
    queue_type: QueueType,
    logger=None,
    debug=False,
    default_path: Enum = None,
):
    if not logger:
        logger = ServerlessLogger()

    logger.debug(f"Event received. queue: {queue_type}, event: {event}")
    try:
        assert isinstance(queue_type, QueueType)
    except AssertionError as e:
        raise InvalidInputError(f"Invalid queue type '{queue_type}'") from e

    successes = 0
    records = get_records_from_event(queue_type, event)
    try:
        assert isinstance(records, list)
    except AssertionError as e:
        logger.error(f"'records' is not a list {e}")
        return build_response(0, 0, logger)

    output = []
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
                payload = Payload(_path, _kwargs).validate(path_enum)
            except AssertionError as e:
                raise InvalidInputError(
                    "'path' or 'kwargs' missing from payload."
                ) from e
            except TypeError as e:
                raise InvalidInputError(
                    f"Bad record provided for queue type {queue_type}. {encoded_record}"
                ) from e

            with logger.context(bind={"payload": payload.to_dict()}):
                logger.log(f"Record received.")

            ret = execute_payload(
                payload=payload, path_enum=path_enum, paths=paths, logger=logger
            )
            successes += 1
        except InvalidInputError as e:
            logger.error(str(e))
            sentry.capture(e)
            continue  # Drop poisoned records on the floor.
        except InvalidPathError as e:
            logger.error(f"Payload specified an invalid path. {e}")
            sentry.capture(e)
            continue
        except json.JSONDecodeError as e:
            logger.error(f"Payload contained invalid json. {e}")
            sentry.capture(e)
            continue
        except FailButContinue as e:
            # successes += 0
            logger.debug(str(e))
            sentry.capture(e)
            continue  # user can say "bad thing happened but keep going"
        except FailCatastrophically:
            raise
        output.append(ret)

    response = build_response(n_records=len(records), n_ok=successes, logger=logger)
    if any(output):
        response["output"] = output
    if debug:
        response["debug"] = json.dumps(records, cls=AutoEncoder)
    return response


def execute_path(path, kwargs, logger, path_enum, paths):
    warnings.warn(
        "execute_path is deprecated in favor of execute_payload", DeprecationWarning
    )
    payload = Payload(path, kwargs).validate(path_enum)
    return execute_payload(payload, path_enum, paths, logger)


def execute_payload(payload: Payload, path_enum: EnumMeta, paths: dict, logger):
    """Execute functions, paths, and shortcuts in a Path."""
    if not logger:
        logger = ServerlessLogger()

    ret = None

    if isinstance(payload.path, str):
        payload.path = get_enum_value(path_enum, payload.path)

    if isinstance(payload.path, Enum):  # PATH
        for action in paths[payload.path]:
            assert isinstance(action, Action)

            # Build action kwargs and validate type hints
            try:
                action_kwargs = build_action_kwargs(
                    action, {"logger": None, **payload.kwargs}
                )
                action_kwargs.pop("logger", None)
            except (TypeError, AssertionError) as e:
                raise InvalidInputError(
                    f"Failed to run {payload.path.name} {action} due to {e}"
                ) from e

            # Run action functions
            for f in action.functions:
                assert isinstance(f, FunctionType)
                try:
                    # TODO: if ret, set _last_output
                    with logger.context(
                        bind={
                            "kwargs": action_kwargs,
                            "path": payload.path.name,
                            "function": f.__name__,
                        }
                    ):
                        logger.log("Executing function.")
                        ret = f(**{**action_kwargs, "logger": logger})

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
                            raise FailButContinue(
                                f"Something went wrong while extracting Payloads from a function return value. {ret}"
                            ) from e

                        for p in _payloads:
                            logger.debug(f"Function returned a Payload. Executing. {p}")
                            try:
                                ret = execute_payload(p, path_enum, paths, logger)
                            except Exception as e:
                                raise FailButContinue(
                                    f"Failed to execute returned Payload. {p}"
                                ) from e
                except (
                    FailButContinue,
                    FailCatastrophically,
                    InvalidInputError,
                    InvalidPathError,
                    json.JSONDecodeError,
                ):
                    raise
                except Exception as e:
                    logger.error(
                        f"Skipped {payload.path.name} {f.__name__} due to unhandled Exception. This is very serious; please update your function to handle this. Reason: {e}"
                    )
                    sentry.capture(e)

            # Run action paths / shortcuts
            for path_descriptor in action.paths:
                _payload = Payload(path_descriptor, action_kwargs)
                ret = execute_payload(_payload, path_enum, paths, logger)
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


def build_action_kwargs(action: namedtuple, kwargs: dict) -> dict:
    """Build dictionary of kwargs for a specific action.

    Args:
        action (namedtuple)
        kargs (dict): kwargs provided in the event's message

    Returns:
        dict: validated kwargs required by action
    """
    action_kwargs = {}
    if not action.required_params and action.functions:
        action_kwargs = validate_signature(action.functions, kwargs)
    elif action.required_params and isinstance(action.required_params, list):
        for param in action.required_params:
            param_name = param[0] if isinstance(param, tuple) else param
            try:
                # Assert required field was provided.
                assert param_name in kwargs
            except AssertionError as e:
                raise InvalidInputError(f"Missing param '{param_name}'") from e

            # Set param in kwargs. If the param is a tuple, use the [1] as the new key.
            if isinstance(param, tuple) and len(param) == 2:
                action_kwargs[param[1]] = kwargs[param[0]]
            else:
                action_kwargs[param] = kwargs[param]
    elif not action.required_params:
        return {}
    else:
        raise InvalidInputError(
            "You either didn't provide functions or required_params was not an instance of list or NoneType."
        )

    return action_kwargs


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


def get_payload_from_record(queue_type: QueueType, record, validate=True) -> dict:
    if queue_type == QueueType.RAW:
        payload = get_raw_payload(record)
    if queue_type == QueueType.KINESIS:
        payload = get_kinesis_payload(record)
    if queue_type == QueueType.SQS:
        payload = get_sqs_payload(record)
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
