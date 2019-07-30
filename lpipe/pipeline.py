import base64
import importlib
import json
import logging
import shlex
from collections import namedtuple
from enum import Enum

import requests
from decouple import config

from lpipe import kinesis, sqs
from lpipe.exceptions import InvalidInputError, InvalidPathError, GraphQLError
from lpipe.logging import ServerlessLogger
from lpipe.utils import get_nested, batch

Action = namedtuple("Action", "required_params functions paths")


class QueueType(Enum):
    KINESIS = 1
    SQS = 2


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


def build_response(n_records, n_ok, logger):
    response = {
        "event": "Finished.",
        "stats": {"received": n_records, "successes": n_ok},
    }
    if hasattr(logger, "events") and logger.events:
        response["logs"] = logger.events
    return response


def process_event(event, path_enum, paths, queue_type, logger=None):
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

    for record in records:
        try:
            try:
                payload = get_payload_from_record(queue_type, record)
            except AssertionError as e:
                raise InvalidInputError(
                    "'path' or 'kwargs' missing from payload."
                ) from e
            except TypeError as e:
                raise InvalidInputError(
                    f"Bad record provided for queue type {queue_type}. {record}"
                ) from e

            with logger.context(bind={"payload": payload}):
                logger.log(f"Record received.")
            execute_path(
                path=payload["path"],
                kwargs=payload["kwargs"],
                logger=logger,
                path_enum=path_enum,
                paths=paths,
            )
            successes += 1
        except InvalidInputError as e:
            logger.error(str(e))
            continue  # Drop poisoned records on the floor.
        except InvalidPathError as e:
            logger.error(f"Payload specified an invalid path. {e}")
            continue
        except json.JSONDecodeError as e:
            logger.error(f"Payload contained invalid json. {e}")
            continue

    return build_response(n_records=len(records), n_ok=successes, logger=logger)


def execute_path(path, kwargs, logger, path_enum, paths):
    """Execute functions, paths, and shortcuts in a Path."""
    if not logger:
        logger = ServerlessLogger()

    if isinstance(path, Enum) or isinstance(path, str):  # PATH
        try:
            path = path_enum[str(path).split(".")[-1]]
        except KeyError as e:
            raise InvalidPathError(e)

        for action in paths[path]:
            assert isinstance(action, Action)

            # Build action kwargs
            action_kwargs = {}
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

            # Run action functions
            for f in action.functions:
                try:
                    with logger.context(
                        bind={
                            "kwargs": action_kwargs,
                            "path": path.name,
                            "function": f.__name__,
                        }
                    ):
                        logger.log("Executing function.")
                        f(logger=logger, **action_kwargs)
                except Exception as e:
                    logger.error(f"Skipped {path.name} {f.__name__} because: {e}")

            # Run action paths / shortcuts
            for path_descriptor in action.paths:
                execute_path(path_descriptor, action_kwargs, logger, path_enum, paths)
    elif isinstance(path, Queue):  # SHORTCUT
        queue = path
        assert isinstance(queue.type, QueueType)
        with logger.context(
            bind={
                "path": queue.path,
                "queue_type": queue.type,
                "queue_name": queue.name,
                "kwargs": kwargs,
            }
        ):
            logger.log("Pushing record.")
        put_record(queue=queue, record={"path": queue.path, "kwargs": kwargs})
    else:
        logger.info(f"Path should be a string, Path, or Queue {path})")


def get_kinesis_payload(record, required_fields=["path", "kwargs"]):
    """Decode and validate a kinesis record."""
    assert record["kinesis"]["data"] is not None
    payload = json.loads(
        base64.b64decode(bytearray(record["kinesis"]["data"], "utf-8"))
    )
    for field in required_fields:
        assert field in payload
    return payload


def get_sqs_payload(record, required_fields=["path", "kwargs"]):
    """Decode and validate an sqs record."""
    assert record["body"] is not None
    payload = json.loads(record["body"])
    for field in required_fields:
        assert field in payload
    return payload


def get_records_from_event(queue_type, event):
    if queue_type == QueueType.KINESIS:
        return event["Records"]
    if queue_type == QueueType.SQS:
        return event["Records"]


def get_payload_from_record(queue_type, record):
    if queue_type == QueueType.KINESIS:
        return get_kinesis_payload(record)
    if queue_type == QueueType.SQS:
        return get_sqs_payload(record)


def put_record(queue, record):
    if queue.type == QueueType.KINESIS:
        return kinesis.put_record(stream_name=queue.name, data=record)
    elif queue.type == QueueType.SQS:
        if queue.name and not queue.url:
            queue.url = sqs.get_queue_url(queue.name)
        return sqs.put_message(queue_url=queue.url, message=record)
