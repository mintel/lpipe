from enum import Enum

from decouple import config
from mintel_logging.logger import get_logger

from lpipe.pipeline import Action, Queue, Input, process_event
from lpipe.utils import check_sentry


class Path(Enum):
    TEST_FUNC = 1
    TEST_FUNC_NO_PARAMS = 2
    TEST_PATH = 3
    TEST_FUNC_AND_PATH = 4
    TEST_KINESIS_PATH = 5
    TEST_NO_PARAMS = 6
    TEST_RENAME_PARAM = 7


PATHS = {
    Path.TEST_FUNC: [
        Action(required_params=["foo"], functions=["test_func"], paths=[])
    ],
    Path.TEST_FUNC_NO_PARAMS: [
        Action(required_params=[], functions=["test_func_no_params"], paths=[])
    ],
    Path.TEST_PATH: [
        Action(required_params=["foo"], functions=[], paths=[Path.TEST_FUNC])
    ],
    Path.TEST_FUNC_AND_PATH: [
        Action(required_params=["foo"], functions=["test_func"], paths=[Path.TEST_FUNC])
    ],
    # Path.TEST_KINESIS_PATH: [
    #    Action(
    #        required_params=["uri"],
    #        functions=[],
    #        paths=[Queue(name=config("SECOND_TEST_KINESIS_STREAM"), type=Input.KINESIS, path="TEST_FUNC")],
    #    )
    # ],
    Path.TEST_FUNC_NO_PARAMS: [
        Action(required_params=[], functions=["test_func_no_params"], paths=[]),
        Action(
            required_params=[],
            functions=["test_func_no_params"],
            paths=[Path.TEST_FUNC_NO_PARAMS],
        ),
        Action(required_params=[], functions=[], paths=[Path.TEST_FUNC_NO_PARAMS]),
    ],
    Path.TEST_RENAME_PARAM: [
        Action(
            required_params=[
                ("bar", "foo")
            ],  # Tuples indicate the param should be mapped to a different name.
            functions=["test_func"],
            paths=[],
        )
    ],
    #    Path.TEST_SQS_PATH: [
    #        Action(
    #            required_params=["uri"],
    #            functions=[],
    #            paths=[Queue(name=config("TEST_SQS_STREAM"), type=Input.SQS, path="TEST_FUNC")],
    #        )
    #    ],
}


def lambda_handler(event, context):
    logger = get_logger("", "dummy-lambda")
    return process_event(event, logger, Path, PATHS)


def test_func(foo, logger, **kwargs):
    if not foo:
        raise Exception("Missing required parameter 'foo'")
    logger.log("test_func success")
    return True


def test_func_no_params(logger, **kwargs):
    logger.log("test_func_no_params success")
    return True
