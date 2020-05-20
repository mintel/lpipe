import json

from lpipe.logging import LPLogger
from lpipe.testing.utils import emit_logs
from lpipe.utils import AutoEncoder


def test_create_logger():
    logger = LPLogger()
    assert isinstance(logger, LPLogger)


def test_logger_log():
    logger = LPLogger()
    logger.log("Test log.")


def test_logger_log_info():
    logger = LPLogger()
    logger.info("Test info.")


def test_logger_log_warning():
    logger = LPLogger()
    logger.warning("Test warning.")


def test_logger_log_error():
    logger = LPLogger()
    logger.error("Test error.")


def test_logger_log_critical():
    logger = LPLogger()
    logger.critical("Test critical.")


def test_create_logger_persist():
    logger = LPLogger()
    logger.persist = True
    assert isinstance(logger, LPLogger)


def test_logger_persist_events():
    logger = LPLogger()
    logger.persist = True
    logger.log("TEST")
    for e in logger.events:
        assert e["event"] == "TEST"


def test_logger_persist_events_context():
    logger = LPLogger()
    logger.persist = True
    with logger.context(bind={"foo": "bar"}):
        logger.log("TEST")
    for e in logger.events:
        # {"level": level, "event": event, "context": self._logger._context}
        assert e["event"] == "TEST"
        assert e["context"] == {"foo": "bar"}


def test_logger_persist_emit():
    logger = LPLogger()
    logger.persist = True
    with logger.context(bind={"foo": "bar"}):
        logger.log("TEST")
    body = {"logs": logger.events}
    emit_logs(body)


def test_logger_context_action():
    logger = LPLogger()
    with logger.context(bind={"foo": "bar"}, action="my_action"):
        logger.log("TEST")


def test_logger_bind_unbind():
    logger = LPLogger()
    logger.bind(foo="bar")
    logger.unbind("foo")


def test_encode_logger():
    logger = LPLogger()
    json.dumps(logger, cls=AutoEncoder)
