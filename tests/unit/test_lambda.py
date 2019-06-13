import logging
from enum import Enum

import pytest

from lpipe.logging import ServerlessLogger
from lpipe.pipeline import Action, QueueType, process_event
from tests.integration.dummy_lambda import src

LOGGER = logging.getLogger()


def _emit_logs(body):
    if "logs" in body:
        for log in body["logs"]:
            LOGGER.log(level=logging.INFO, msg=log["event"])


class Path(Enum):
    TEST_FUNC = 1
    TEST_FUNC_NO_PARAMS = 2
    TEST_PATH = 3
    TEST_FUNC_AND_PATH = 4
    MULTI_TEST_FUNC_NO_PARAMS = 5
    TEST_RENAME_PARAM = 6


PATHS = {
    Path.TEST_FUNC: [
        Action(required_params=["foo"], functions=[src.test_func], paths=[])
    ],
    Path.TEST_FUNC_NO_PARAMS: [
        Action(required_params=[], functions=[src.test_func_no_params], paths=[])
    ],
    Path.TEST_PATH: [
        Action(required_params=["foo"], functions=[], paths=[Path.TEST_FUNC])
    ],
    Path.TEST_FUNC_AND_PATH: [
        Action(
            required_params=["foo"], functions=[src.test_func], paths=[Path.TEST_FUNC]
        )
    ],
    Path.MULTI_TEST_FUNC_NO_PARAMS: [
        Action(required_params=[], functions=[src.test_func_no_params], paths=[]),
        Action(
            required_params=[],
            functions=[src.test_func_no_params],
            paths=[Path.TEST_FUNC_NO_PARAMS],
        ),
        Action(required_params=[], functions=[], paths=[Path.TEST_FUNC_NO_PARAMS]),
    ],
    Path.TEST_RENAME_PARAM: [
        Action(
            required_params=[
                ("bar", "foo")
            ],  # Tuples indicate the param should be mapped to a different name.
            functions=[src.test_func],
            paths=[],
        )
    ],
}


def test_process_event_empty(kinesis_payload):
    logger = ServerlessLogger(level=logging.DEBUG, process="dummy-lambda")
    logger.persist = True
    payload = []
    response = process_event(
        event=kinesis_payload(payload),
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
        logger=logger,
    )
    _emit_logs(response)
    assert "event" in response
    assert "stats" in response
    assert "logs" in response
    assert response["stats"]["received"] == 0
    assert response["stats"]["successes"] == 0
    for log in response["logs"]:
        assert log["level"] != logging.ERROR


def test_process_event_empty_payload(kinesis_payload):
    logger = ServerlessLogger(level=logging.DEBUG, process="dummy-lambda")
    logger.persist = True
    payload = [{}]
    response = process_event(
        event=kinesis_payload(payload),
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
        logger=logger,
    )
    _emit_logs(response)
    assert response["stats"]["received"] == 1
    assert response["stats"]["successes"] == 0


def test_process_event_func(kinesis_payload):
    logger = ServerlessLogger(level=logging.DEBUG, process="dummy-lambda")
    logger.persist = True
    payload = [{"path": "TEST_FUNC", "kwargs": {"foo": "bar"}}]
    response = process_event(
        event=kinesis_payload(payload),
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
        logger=logger,
    )
    _emit_logs(response)
    assert response["stats"]["received"] == 1
    assert response["stats"]["successes"] == 1


def test_process_event_func_no_params(kinesis_payload):
    logger = ServerlessLogger(level=logging.DEBUG, process="dummy-lambda")
    logger.persist = True
    payload = [{"path": "TEST_FUNC_NO_PARAMS", "kwargs": {}}]
    response = process_event(
        event=kinesis_payload(payload),
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
        logger=logger,
    )
    _emit_logs(response)
    assert response["stats"]["received"] == 1
    assert response["stats"]["successes"] == 1


def test_process_event_path(kinesis_payload):
    logger = ServerlessLogger(level=logging.DEBUG, process="dummy-lambda")
    logger.persist = True
    payload = [{"path": "TEST_PATH", "kwargs": {"foo": "bar"}}]
    response = process_event(
        event=kinesis_payload(payload),
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
        logger=logger,
    )
    _emit_logs(response)
    assert response["stats"]["received"] == 1
    assert response["stats"]["successes"] == 1


def test_process_event_func_and_path(kinesis_payload):
    logger = ServerlessLogger(level=logging.DEBUG, process="dummy-lambda")
    logger.persist = True
    payload = [{"path": "TEST_FUNC_AND_PATH", "kwargs": {"foo": "bar"}}]
    response = process_event(
        event=kinesis_payload(payload),
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
        logger=logger,
    )
    _emit_logs(response)
    assert response["stats"]["received"] == 1
    assert response["stats"]["successes"] == 1


def test_process_event_multi_func_no_params(kinesis_payload):
    logger = ServerlessLogger(level=logging.DEBUG, process="dummy-lambda")
    logger.persist = True
    payload = [{"path": "MULTI_TEST_FUNC_NO_PARAMS", "kwargs": {}}]
    response = process_event(
        event=kinesis_payload(payload),
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
        logger=logger,
    )
    _emit_logs(response)
    assert response["stats"]["received"] == 1
    assert response["stats"]["successes"] == 1


def test_process_event_rename_param(kinesis_payload):
    logger = ServerlessLogger(level=logging.DEBUG, process="dummy-lambda")
    logger.persist = True
    payload = [{"path": "TEST_RENAME_PARAM", "kwargs": {"bar": "bar"}}]
    response = process_event(
        event=kinesis_payload(payload),
        path_enum=Path,
        paths=PATHS,
        queue_type=QueueType.KINESIS,
        logger=logger,
    )
    _emit_logs(response)
    assert response["stats"]["received"] == 1
    assert response["stats"]["successes"] == 1
