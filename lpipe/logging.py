import logging
import time
from contextlib import ContextDecorator

import structlog
from decouple import config
from structlog import wrap_logger
from structlog.processors import JSONRenderer, TimeStamper

import lpipe.exceptions
from lpipe import utils


class LPLogger:
    def __init__(self, level=logging.INFO, **kwargs):
        self._logger = wrap_logger(
            structlog.get_logger(),
            processors=[TimeStamper(fmt="iso"), JSONRenderer(sort_keys=True)],
        )
        self.level = level
        self.bind(**kwargs)
        self.events = []
        self.persist = False

    def _json(self):
        return utils.repr(self)

    def bind(self, **kwargs):
        """Bind context data to logger by forwarding to structlog.

        Args:
            **kwargs: keyword arguments/context dict

        Returns:
            self

        """
        self._logger = self._logger.bind(**kwargs)
        return self

    def unbind(self, *keys):
        """Unbind context data from logger by forwarding to structlog.

        Args:
            *keys: list of keys to unbind

        Returns:
            None

        """
        self._logger = self._logger.unbind(*keys)
        return self

    def _log(self, event, **kwargs):
        return self._logger.msg(event, **kwargs)

    def context(self, action=None, bind=None):
        """
        Return a LoggerContext that saves+restores state, optionally with binding, and duration logging.

        Args:
            action (str): if provided, a start log will be made on entry, and finish log with duration on exit
            bind (dict): if provided, these values will be bound to the logger while the context is active
        """
        return LoggerContext(self, action, bind, level=self.level)

    def log(self, event, level=logging.INFO, **kwargs):
        """Log an event to the logger. Records log level as a context variable.

        Args:
            event (str): Event string
            level (int): Level to log the event
            kwargs: arbitrary key value pairs

        Returns:
            log data

        """
        if level < self.level:
            return
        else:
            if self.persist:
                event = {
                    "level": level,
                    "event": event,
                    "context": self._logger._context,
                }
                self.events.append(event)
            return self._log(event, level=level, **kwargs)

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


class LoggerContext(ContextDecorator):
    """
    Context manager which saves+restores a logger's state, and optionally binds, and logs start+finish with duration.

    """

    def __init__(self, log, action=None, bind=None, level=logging.INFO):
        self.action = action
        self.bind = bind
        self.log = log
        self.level = level
        self.initial_log_logger = None
        self.start = None
        self.on_the_fly = {}

    def __enter__(self):
        """Enter and record the logger's original state"""
        self.start = time.time()
        self.initial_log_logger = self.log._logger
        if self.bind:
            self.log.bind(**self.bind)
        if self.action:
            self.log.log("start:%s" % self.action, level=self.level)
        return self.on_the_fly

    def __exit__(self, *exc):
        """Exit and return the logger to its original state"""
        now = time.time()
        if self.action:
            self.log.bind(duration=now - self.start)
            self.log.bind(**self.on_the_fly)
            self.log.log("finish:%s" % self.action, level=self.level)
        self.log._logger = self.initial_log_logger
        self.initial_log_logger = None
        self.start = None


def setup(context, logger=None, debug: bool = False):
    try:
        if not logger:
            logger = LPLogger(
                level=logging.DEBUG if debug else logging.INFO,
                process=getattr(
                    context, "function_name", config("FUNCTION_NAME", default=None)
                ),
            )

        if debug and isinstance(logger, LPLogger):
            logger.persist = True
    except Exception as e:
        raise lpipe.exceptions.InvalidConfigurationError(
            "Failed to initialize logger."
        ) from e
    return logger
