import base64
import importlib
import json
import shlex
from collections import namedtuple
from enum import Enum

import requests
from decouple import config
from raven.contrib.awslambda import LambdaClient

from exceptions import InvalidInput, InvalidPathException, GraphQLException
from kinesis import put_record
from utils import get_module_attr, get_nested, batch


INPUT_TYPE = config("INPUT_TYPE", "kinesis")

Action = namedtuple(
    'Action',
    'required_params functions paths'
)


def process_records(records, logger, path_enum, paths):
    successes = 0
    for record in records:
        try:
            if INPUT_TYPE == "kinesis":
                payload = get_kinesis_payload(record)
            if INPUT_TYPE == "sqs":
                raise Exception("SQS not yet implemented.")
            else:
                raise Exception(f"Unsupported INPUT_TYPE: {INPUT_TYPE}")
            with logger.context(bind={'payload': payload}):
                logger.log(f'Record received.')
            execute_path(
                path=payload['path'],
                kwargs=payload['kwargs'],
                logger=logger,
                path_enum=path_enum,
                paths=paths,
            )
            successes += 1
        except AssertionError as e:
            logger.log(f'Payload was missing an expected param. {e}')
            continue  # Drop poisoned records on the floor.
        except InvalidPathException as e:
            logger.log(f'Payload specified an invalid path. {e}')
            continue
        except json.JSONDecodeError as e:
            logger.log(f'Payload contained invalid json. {e}')
            continue
    return 'Successfully processed {}/{} records.'.format(successes, len(records))


def get_kinesis_payload(record, required_fields=['path', 'kwargs']):
    """Decode and validate record payload."""
    assert record['kinesis']['data'] is not None
    payload = json.loads(base64.b64decode(record['kinesis']['data']))
    for field in required_fields:
        assert field in payload
    return payload


def execute_path(path, kwargs, logger, path_enum, paths):
    """Execute functions, paths, and shortcuts in a Path."""
    if isinstance(path, Enum) or isinstance(path, str):  # PATH
        try:
            path = path_enum[str(path).split('.')[-1]]
        except KeyError as e:
            raise InvalidPathException(e)
        for action in paths[path]:
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
                    with logger.context(bind={'kwargs': action_kwargs, 'path': path.name, 'function': function}):
                        logger.log(f'Executing function.')
                        get_module_attr(f'main.{function}')(logger=logger, **action_kwargs)
                except InvalidInput as e:
                    logger.log(f'Skipped {path.name} {function} because: {e}')

            # Run action paths / shortcuts
            for path_name in action.paths:
                execute_path(path_name, action_kwargs, logger, path_enum, paths)
    elif isinstance(path, tuple):  # SHORTCUT
        stream_name = path[0]
        path = path[1]
        with logger.context(bind={'path': path, 'stream_name': stream_name, 'kwargs': kwargs}):
            logger.log(f'Pushing record to stream.')
        put_record(
            stream_name=stream_name,
            data={
                'path': path,
                'kwargs': kwargs,
            }
        )
    else:
        logger.log(f'Invalid tuple, str, or enum value. (path: {path})')
