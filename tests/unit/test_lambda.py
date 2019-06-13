import logging
from enum import Enum

import pytest

from lpipe.logging import ServerlessLogger
from lpipe.pipeline import Action, QueueType, process_event


LOGGER = logging.getLogger()

def _emit_logs(body):
    if "logs" in body:
        for log in body["logs"]:
            LOGGER.log(level=logging.INFO, msg=log["event"])

class Path(Enum):
    TEST_FUNC = 1

PATHS = {
    Path.TEST_FUNC: [
        Action(required_params=["foo"], functions=[], paths=[])
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
    #assert 1==2


def test_process_event_valid_payload(kinesis_payload):
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
