from enum import Enum

import sentry_sdk
from decouple import config
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from lpipe.logging import ServerlessLogger
from lpipe.pipeline import Action, Queue, QueueType, process_event


def test_func(foo, logger, **kwargs):
    if not foo:
        raise Exception("Missing required parameter 'foo'")
    logger.log("test_func success")
    return True


def test_func_no_params(logger, **kwargs):
    logger.log("test_func_no_params success")
    return True


class Path(Enum):
    TEST_FUNC = 1
    TEST_FUNC_NO_PARAMS = 2
    TEST_PATH = 3
    TEST_FUNC_AND_PATH = 4
    MULTI_TEST_FUNC_NO_PARAMS = 5
    TEST_RENAME_PARAM = 6
    TEST_KINESIS_PATH = 7
    TEST_SQS_PATH = 8


PATHS = {
    Path.TEST_FUNC: [Action(required_params=["foo"], functions=[test_func], paths=[])],
    Path.TEST_FUNC_NO_PARAMS: [
        Action(required_params=[], functions=[test_func_no_params], paths=[])
    ],
    Path.TEST_PATH: [
        Action(required_params=["foo"], functions=[], paths=[Path.TEST_FUNC])
    ],
    Path.TEST_FUNC_AND_PATH: [
        Action(required_params=["foo"], functions=[test_func], paths=[Path.TEST_FUNC])
    ],
    Path.MULTI_TEST_FUNC_NO_PARAMS: [
        Action(required_params=[], functions=[test_func_no_params], paths=[]),
        Action(
            required_params=[],
            functions=[test_func_no_params],
            paths=[Path.TEST_FUNC_NO_PARAMS],
        ),
        Action(required_params=[], functions=[], paths=[Path.TEST_FUNC_NO_PARAMS]),
    ],
    Path.TEST_RENAME_PARAM: [
        Action(
            required_params=[
                ("bar", "foo")
            ],  # Tuples indicate the param should be mapped to a different name.
            functions=[test_func],
            paths=[],
        )
    ],
    Path.TEST_KINESIS_PATH: [
        Action(
            required_params=["uri"],
            functions=[],
            paths=[
                Queue(
                    name=config("TEST_KINESIS_STREAM"),
                    type=QueueType.KINESIS,
                    path="TEST_FUNC",
                )
            ],
        )
    ],
    Path.TEST_SQS_PATH: [
        Action(
            required_params=["uri"],
            functions=[],
            paths=[
                Queue(
                    name=config("TEST_SQS_QUEUE"), type=QueueType.SQS, path="TEST_FUNC"
                )
            ],
        )
    ],
}


def lambda_handler(event, context):
    sentry_sdk.init(dsn=config("SENTRY_DSN"), integrations=[AwsLambdaIntegration()])

    # logger.persist is designed for debug use.
    # Stores all logs in the logger and adds them to the function response.
    logger = ServerlessLogger(process="dummy-lambda")
    logger.persist = True

    return process_event(
        event=event,
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
        logger=logger,
    )
