import base64
import importlib
import json
import logging
import shlex
from collections import namedtuple
from enum import Enum

import requests
from decouple import config
from raven.contrib.awslambda import LambdaClient

from lpipe import kinesis
from lpipe.exceptions import InvalidInput, InvalidPathException, GraphQLException
from lpipe.logging import ServerlessLogger
from lpipe.utils import get_module_attr, get_nested, batch


class Input(Enum):
    KINESIS = 1
    SQS = 2


Action = namedtuple("Action", "required_params functions paths")
Queue = namedtuple("Queue", "type name path")


def process_event(event, path_enum, paths, logger=None):
    if not logger:
        logger = ServerlessLogger()

    #lc = LogCatcher(logger, log_handler)
    #_log = lc._log

    INPUT_TYPE = config("INPUT_TYPE", Input.KINESIS)
    successes = 0

    # TODO: get records differently based on queue
    # Maybe combine get_QUEUE_payload() funcs and this into a generator
    records = event["Records"]

    for record in records:
        try:
            assert INPUT_TYPE in Input
            if INPUT_TYPE == Input.KINESIS:
                payload = get_kinesis_payload(record)
            if INPUT_TYPE == Input.SQS:
                payload = get_sqs_payload(record)

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
        except AssertionError as e:
            logger.warning(f"Payload was missing an expected param. {e}")
            continue  # Drop poisoned records on the floor.
        except InvalidPathException as e:
            logger.warning(f"Payload specified an invalid path. {e}")
            continue
        except json.JSONDecodeError as e:
            logger.warning(f"Payload contained invalid json. {e}")
            continue

    n_records = len(records)
    response = {
        "event": "Finished.",
        "stats": {"received": n_records, "successes": successes},
    }
    #if lc.messages:
    #    response["logs"] = lc.messages
    return response


def get_kinesis_payload(record, required_fields=["path", "kwargs"]):
    """Decode and validate a kinesis record."""
    assert record["kinesis"]["data"] is not None
    payload = json.loads(base64.b64decode(bytearray(record["kinesis"]["data"], "utf-8")))
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


def execute_path(path, kwargs, logger, path_enum, paths):
    """Execute functions, paths, and shortcuts in a Path."""
    if isinstance(path, Enum) or isinstance(path, str):  # PATH
        try:
            path = path_enum[str(path).split(".")[-1]]
        except KeyError as e:
            raise InvalidPathException(e)
        for action in paths[path]:
            assert isinstance(action, Action)

            # Build action kwargs
            action_kwargs = {}

            for param in action.required_params:
                # Assert required field was provided.
                assert (param[0] if isinstance(param, tuple) else param) in kwargs

                # Set param in kwargs. If the param is a tuple, use the [1] as the new key.
                if isinstance(param, tuple) and len(param) == 2:
                    action_kwargs[param[1]] = kwargs[param[0]]
                else:
                    action_kwargs[param] = kwargs[param]

            # Run action functions
            for function in action.functions:
                try:
                    with logger.context(
                        bind={
                            "kwargs": action_kwargs,
                            "path": path.name,
                            "function": function,
                        }
                    ):
                        logger.log(f"Executing function.")
                        get_module_attr(f"main.{function}")(
                            logger=logger, **action_kwargs
                        )
                except InvalidInput as e:
                    logger.log(f"Skipped {path.name} {function} because: {e}")

            # Run action paths / shortcuts
            for path_descriptor in action.paths:
                execute_path(path_descriptor, action_kwargs, logger, path_enum, paths)
    elif isinstance(path, Queue):  # SHORTCUT
        q = path
        assert q.type in Input

        with logger.context(
            bind={
                "path": q.path,
                "queue_type": q.type,
                "queue_name": q.name,
                "kwargs": kwargs,
            }
        ):
            logger.log("Pushing record.")

        if q.type == Input.KINESIS:
            kinesis.put_record(
                stream_name=q.name, data={"path": q.path, "kwargs": kwargs}
            )
        elif q.type == Input.SQS:
            raise Exception("SQS not yet implemented.")
    else:
        logger.error(f"Path should be a string, Path, or Queue {path})")
