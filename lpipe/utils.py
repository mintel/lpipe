import base64
import hashlib
import importlib
import json
import logging
import os
import shlex
import sys
from collections import namedtuple
from contextlib import contextmanager
from enum import Enum
from pathlib import Path

import requests

from lpipe.exceptions import InvalidInputError, InvalidPathError


def hash(encoded_data):
    return hashlib.sha1(encoded_data.encode("utf-8")).hexdigest()


def batch(iterable, n=1):
    """Batch iterator.

    https://stackoverflow.com/a/8290508

    """
    iter_len = len(iterable)
    for ndx in range(0, iter_len, n):
        yield iterable[ndx : min(ndx + n, iter_len)]


def get_nested(d, keys):
    """Given a dictionary, fetch a key nested several levels deep."""

    def _get(head, k):
        if isinstance(head, dict):
            return head.get(k, {})
        else:
            return getattr(head, k, {})

    head = d
    for k in keys:
        head = _get(head, k)
        if not head:
            return head
    return head


def set_nested(d, keys, value):
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def _set_env(env):
    state = {}
    for k, v in env.items():
        state[k] = os.environ[k] if k in os.environ else None
        os.environ[k] = str(v)
        logging.getLogger().debug(f"os.environ[{k}] = {v}")
    return state


def _reset_env(env, state):
    for k, v in env.items():
        if k in state and state[k]:
            os.environ[k] = str(state[k])
        elif k in os.environ:
            del os.environ[k]


@contextmanager
def set_env(env):
    state = {}
    try:
        state = _set_env(env)
        yield
    finally:
        _reset_env(env, state)


def emit_logs(body, logger=None):
    logger = logger if logger else logging.getLogger()
    if isinstance(body, dict) and "logs" in body:
        try:
            logs = json.loads(body["logs"])
        except TypeError:
            logs = body["logs"]
        for log in logs:
            logger.info(f"{log}")
    elif isinstance(body, str):
        logger.log(level=logging.INFO, msg=body)


class AutoEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, Enum):
                return str(obj)
            return obj._json()
        except AttributeError:
            return json.JSONEncoder.default(self, obj)
