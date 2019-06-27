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
    head = d
    for k in keys:
        head = head.get(k, {})
        if not head:
            return head
    return head


@contextmanager
def set_env(env):
    state = {}
    try:
        for k, v in env.items():
            state[k] = os.environ[k] if k in os.environ else None
            os.environ[k] = str(v)
            print(f"os.environ[{k}] = {v}")
        yield
    finally:
        for k, v in env.items():
            if k in state and state[k]:
                os.environ[k] = str(state[k])
            elif k in os.environ:
                del os.environ[k]


def emit_logs(body, logger=None):
    logger = logger if logger else logging.getLogger()
    if "logs" in body:
        for log in body["logs"]:
            logger.log(level=logging.INFO, msg=log["event"])
