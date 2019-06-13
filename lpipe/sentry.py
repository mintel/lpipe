from functools import wraps

from decouple import config
from sentry_sdk import push_scope


def _env(*keys):
    for key in keys:
        val = config(key, default=None)
        if val:
            return val
    return None


def push_context(context):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # https://docs.sentry.io/enriching-error-data/scopes/?platform=python#local-scopes
            with push_scope() as scope:
                for k, v in context.items():
                    scope.set_tag(k, v)
                return func(*args, **kwargs)
        return wrapper
    return decorator
