import logging
from enum import Enum

from decouple import config

from lpipe.pipeline import Action, process_records
from lpipe.utils import check_sentry


class Path(Enum):
    TEST_FUNC = 1
    TEST_PATH = 2
    TEST_FUNC_AND_PATH = 3
    TEST_KINESIS_PATH = 4
    TEST_NO_PARAMS = 5
    TEST_RENAME_PARAM = 6


PATHS = {
    Path.TEST_FUNC: [
        Action(required_params=["foo"], functions=["test_func"], paths=[])
    ],
    Path.TEST_PATH: [Action(required_params=["foo"], functions=[], paths=[Path.FUNC])],
    Path.TEST_FUNC_AND_PATH: [
        Action(required_params=["foo"], functions=["test_func"], paths=[Path.FUNC])
    ],
    Path.TEST_KINESIS_PATH: [
        Action(
            required_params=["uri"],
            functions=[],
            paths=[(config("SECOND_TEST_KINESIS_STREAM"), "TEST_FUNC")],
        )
    ],
    Path.TEST_FUNC_NO_PARAMS: [
        Action(required_params=[], functions=["test_func_no_params"], paths=[]),
        Action(
            required_params=[], functions=["test_func_no_params"], paths=[Path.FUNC]
        ),
        Action(required_params=[], functions=[], paths=[Path.FUNC]),
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
}


def lambda_handler(event, context):
    logger = logging.getLogger()
    return process_records(event["Records"], logger, Path, PATHS)


def test_func(foo, logger, **kwargs):
    if not foo:
        raise Exception("Missing required parameter 'foo'")
    logger.log("test_func success")
    return True


def test_func_no_params(logger, **kwargs):
    logger.log("test_func_no_params success")
    return True
