import base64
import importlib
import json
import shlex
from collections import namedtuple
from enum import Enum

import requests
from raven.contrib.awslambda import LambdaClient

from exceptions import InvalidInput, InvalidPathException, GraphQLException
from kinesis import put_record


def check_sentry(sentry):
    if not isinstance(sentry, LambdaClient):
        raise TypeError('sentry isn\'t instance of LambdaClient. It might be a \
            raven.base.DummyClient if the SENTRY_DSN env var isn\'t set.')


def batch(iterable, n=1):
    """Batch iterator.

    https://stackoverflow.com/a/8290508

    """
    iter_len = len(iterable)
    for ndx in range(0, iter_len, n):
        yield iterable[ndx:min(ndx + n, iter_len)]


def get_nested(d, keys):
    """Given a dictionary, fetch a key nested several levels deep."""
    head = d
    for k in keys:
        head = head.get(k, {})
        if not head:
            return head
    return head


def get_module_attr(import_path):
    frag = import_path.split('.')
    module = importlib.import_module('.'.join(frag[:-1]))
    return getattr(module, frag[-1])
