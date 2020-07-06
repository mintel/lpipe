import logging
from contextlib import contextmanager
from enum import Enum

from decouple import config

from lpipe import Action, Payload, Queue, QueueType, process_event
from lpipe.exceptions import FailButContinue

# from lpipe.contrib import sentry
# sentry.init()


def test_func(foo: str, logger, event, **kwargs):
    if not foo:
        raise Exception("Missing required parameter 'foo'")
    assert event.context.function_name == "my_lambda"
    assert isinstance(event.payload, Payload)
    logger.log("test_func success")
    return True


def test_func_no_params(logger, **kwargs):
    logger.log("test_func_no_params success")
    return True


def test_func_default_param(logger, foo: str = "bar", **kwargs):
    logger.log("test_func_default_param success")
    return True


def test_func_trigger_first(logger, **kwargs):
    return Payload(path=Path.TEST_TRIGGER_SECOND, kwargs={})


def test_func_multi_trigger(logger, **kwargs):
    return [
        Payload(path=Path.TEST_TRIGGER_SECOND, kwargs={}),
        Payload(path=Path.TEST_TRIGGER_SECOND, kwargs={}),
        Payload(
            queue=Queue(
                name=config("TEST_KINESIS_STREAM"),
                type=QueueType.KINESIS,
                path="TEST_FUNC",
            ),
            kwargs={"foo": "bar"},
        ),
    ]


def test_func_trigger_error(logger, **kwargs):
    return Payload(path=Path.TEST_RAISE, kwargs={})


def return_foobar(**kwargs):
    return "foobar"


def test_kwargs_passed_to_default_path_include_all(logger, event, **kwargs):
    try:
        assert kwargs.get("foo", None) == "bar"
    except AssertionError as e:
        raise FailButContinue("foo was not set to bar") from e


def test_kwargs_passed_to_default_path(foo, logger, event, **kwargs):
    try:
        assert foo == "bar"
    except AssertionError as e:
        raise FailButContinue("foo was not set to bar") from e


def throw_exception(**kwargs):
    raise Exception()


#     try:
#         raise Exception("Test event. Please ignore.")
#     except Exception as e:
#         sentry.capture(e)
#         raise FailButContinue from e


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
    TEST_KINESIS_QUEUE = 11
    TEST_SQS_QUEUE = 12
    TEST_SQS_QUEUE_WITHOUT_PATH = 13
    TEST_SENTRY = 14
    TEST_RET = 15
    TEST_TRIGGER_FIRST = 16
    TEST_TRIGGER_SECOND = 17
    TEST_MULTI_TRIGGER = 18
    TEST_TRIGGER_ERROR = 19
    TEST_DEFAULT_PATH = 20
    TEST_DEFAULT_PATH_INCLUDE_ALL = 21
    TEST_BARE_FUNCS = 22
    TEST_RAISE = 23


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
    Path.TEST_BARE_FUNCS: [test_func, test_func_no_params],
    Path.TEST_RENAME_PARAM: [
        Action(
            required_params=[
                ("bar", "foo")
            ],  # Tuples indicate the param should be mapped to a different name.
            functions=[test_func],
        )
    ],
    Path.TEST_KINESIS_QUEUE: [
        Action(
            required_params=["uri"],
            queues=[
                Queue(
                    name=config("TEST_KINESIS_STREAM"),
                    type=QueueType.KINESIS,
                    path="TEST_FUNC",
                )
            ],
        )
    ],
    Path.TEST_SQS_QUEUE: [
        Action(
            required_params=["uri"],
            queues=[
                Queue(
                    name=config("TEST_SQS_QUEUE"), type=QueueType.SQS, path="TEST_FUNC"
                )
            ],
        )
    ],
    Path.TEST_SQS_QUEUE_WITHOUT_PATH: [
        Action(
            required_params=["uri"],
            queues=[Queue(name=config("TEST_SQS_QUEUE"), type=QueueType.SQS)],
        )
    ],
    Path.TEST_FUNC_DEFAULT_PARAM: [Action(functions=[test_func_default_param])],
    Path.TEST_SENTRY: [Action(functions=[throw_exception])],
    Path.TEST_RET: [Action(functions=[return_foobar])],
    Path.TEST_TRIGGER_FIRST: [Action(functions=[test_func_trigger_first])],
    Path.TEST_TRIGGER_SECOND: [Action(functions=[return_foobar])],
    Path.TEST_MULTI_TRIGGER: [Action(functions=[test_func_multi_trigger])],
    Path.TEST_DEFAULT_PATH: [Action(functions=[test_kwargs_passed_to_default_path])],
    Path.TEST_DEFAULT_PATH_INCLUDE_ALL: [
        Action(
            functions=[test_kwargs_passed_to_default_path_include_all],
            include_all_params=True,
        )
    ],
    Path.TEST_TRIGGER_ERROR: [test_func_trigger_error],
    Path.TEST_RAISE: [throw_exception],
}


class StubLogger:
    """
    Normally, a structlog logger is created when one isn't passed in, but some weird
    bug in localstack lambda mocking (in Queue/SHORTCUT block of execute_payload())
    where structlog fails to import itself.
    """

    def __init__(self):
        self.logger = logging.getLogger()

    @contextmanager
    def context(*args, **kwargs):
        yield

    def log(self, event, level=logging.INFO, **kwargs):
        self.logger.log(level, event)

    def debug(self, event, **kwargs):
        return self.log(event, level=logging.DEBUG, **kwargs)

    def info(self, event, **kwargs):
        return self.log(event, level=logging.INFO, **kwargs)

    def warning(self, event, **kwargs):
        return self.log(event, level=logging.WARNING, **kwargs)

    def error(self, event, **kwargs):
        return self.log(event, level=logging.ERROR, **kwargs)

    def critical(self, event, **kwargs):
        return self.log(event, level=logging.CRITICAL, **kwargs)


# @sentry.push_context(
#     {"name": config("FUNCTION_NAME"), "environment": config("APP_ENVIRONMENT")}
# )
def lambda_handler(event, context):
    return process_event(
        event=event,
        context=context,
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.SQS,
        debug=True,
        logger=StubLogger(),
    )
