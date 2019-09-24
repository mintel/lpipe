from enum import Enum

from decouple import config

from lpipe import sentry
from lpipe.exceptions import FailButContinue
from lpipe.logging import ServerlessLogger
from lpipe.pipeline import Action, Queue, QueueType, process_event


sentry.init()


def test_func(foo: str, logger, **kwargs):
    if not foo:
        raise Exception("Missing required parameter 'foo'")
    logger.log("test_func success")
    return True


def test_func_no_params(logger, **kwargs):
    logger.log("test_func_no_params success")
    return True


def test_func_default_param(logger, foo: str = "bar", **kwargs):
    logger.log("test_func_default_param success")
    return True


def throw_exception(**kwargs):
    try:
        raise Exception("Test event. Please ignore.")
    except Exception as e:
        sentry.capture(e)
        raise FailButContinue from e


class Path(Enum):
    TEST_FUNC = 1
    TEST_FUNC_EXPLICIT_PARAMS = 2
    TEST_FUNC_NO_PARAMS = 3
    TEST_FUNC_BLANK_PARAMS = 4
    TEST_FUNC_DEFAULT_PARAM = 5
    TEST_PATH = 6
    TEST_FUNC_AND_PATH = 7
    MULTI_TEST_FUNC = 8
    MULTI_TEST_FUNC_NO_PARAMS = 9
    TEST_RENAME_PARAM = 10
    TEST_KINESIS_PATH = 11
    TEST_SQS_PATH = 12
    TEST_SENTRY = 13


PATHS = {
    Path.TEST_FUNC: [Action(functions=[test_func])],
    Path.TEST_FUNC_EXPLICIT_PARAMS: [
        Action(required_params=["foo"], functions=[test_func])
    ],
    Path.TEST_FUNC_NO_PARAMS: [Action(functions=[test_func_no_params])],
    Path.TEST_FUNC_BLANK_PARAMS: [
        Action(required_params=[], functions=[test_func_no_params])
    ],
    Path.TEST_PATH: [Action(required_params=["foo"], paths=[Path.TEST_FUNC])],
    Path.TEST_FUNC_AND_PATH: [Action(functions=[test_func], paths=[Path.TEST_FUNC])],
    Path.MULTI_TEST_FUNC: [
        Action(functions=[test_func]),
        Action(functions=[test_func], paths=[Path.TEST_FUNC]),
        Action(paths=[Path.TEST_FUNC_BLANK_PARAMS]),
    ],
    Path.MULTI_TEST_FUNC_NO_PARAMS: [
        Action(functions=[test_func_no_params]),
        Action(functions=[test_func_no_params], paths=[Path.TEST_FUNC_BLANK_PARAMS]),
        Action(paths=[Path.TEST_FUNC_BLANK_PARAMS]),
    ],
    Path.TEST_RENAME_PARAM: [
        Action(
            required_params=[
                ("bar", "foo")
            ],  # Tuples indicate the param should be mapped to a different name.
            functions=[test_func],
        )
    ],
    Path.TEST_KINESIS_PATH: [
        Action(
            required_params=["uri"],
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
            paths=[
                Queue(
                    name=config("TEST_SQS_QUEUE"), type=QueueType.SQS, path="TEST_FUNC"
                )
            ],
        )
    ],
    Path.TEST_FUNC_DEFAULT_PARAM: [Action(functions=[test_func_default_param])],
    Path.TEST_SENTRY: [
        Action(required_params=[], functions=[throw_exception], paths=[])
    ],
}


@sentry.push_context(
    {"name": config("FUNCTION_NAME"), "environment": config("APP_ENVIRONMENT")}
)
def lambda_handler(event, context):
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
