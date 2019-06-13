import pytest

from lpipe.logging import ServerlessLogger


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
