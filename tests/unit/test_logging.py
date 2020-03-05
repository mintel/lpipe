import pytest

from lpipe.logging import ServerlessLogger
from lpipe.testing.utils import emit_logs


def test_create_logger():
    logger = ServerlessLogger()
    assert isinstance(logger, ServerlessLogger) == True


def test_logger_log():
    logger = ServerlessLogger()
    logger.log("Test log.")


def test_logger_log_info():
    logger = ServerlessLogger()
    logger.info("Test info.")


def test_logger_log_error():
    logger = ServerlessLogger()
    logger.error("Test error.")


def test_create_logger_persist():
    logger = ServerlessLogger()
    logger.persist = True
    assert isinstance(logger, ServerlessLogger) == True


def test_logger_persist_events():
    logger = ServerlessLogger()
    logger.persist = True
    logger.log("TEST")
    for e in logger.events:
        assert e["event"] == "TEST"


def test_logger_persist_events_context():
    logger = ServerlessLogger()
    logger.persist = True
    with logger.context(bind={"foo": "bar"}):
        logger.log("TEST")
    for e in logger.events:
        # {"level": level, "event": event, "context": self._logger._context}
        assert e["event"] == "TEST"
        assert e["context"] == {"foo": "bar"}


def test_logger_persist_emit():
    logger = ServerlessLogger()
    logger.persist = True
    with logger.context(bind={"foo": "bar"}):
        logger.log("TEST")
    body = {"logs": logger.events}
    emit_logs(body)
