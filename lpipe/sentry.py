from contextlib import contextmanager
from functools import wraps

from decouple import config
from sentry_sdk import capture_exception, configure_scope, init as _init, push_scope
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


def _set_tags(scope, context):
    for k, v in context.items():
        scope.set_tag(k, v)


def init(dsn: str = None, context: dict = None):
    if not dsn:
        dsn = config("SENTRY_DSN")
    _init(dsn=dsn, integrations=[AwsLambdaIntegration()])
    if context:
        with configure_scope() as scope:
            _set_tags(scope, context)


def _env(*keys):
    for key in keys:
        val = config(key, default=None)
        if val:
            return val
    return None


@contextmanager
def scope(context):
    # https://docs.sentry.io/enriching-error-data/scopes/?platform=python#local-scopes
    if config("SENTRY_DSN", default=None):
        with push_scope() as scope:
            _set_tags(scope, context)
            yield


def push_context(context):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with scope(context):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def capture(e):
    if config("SENTRY_DSN", default=None):
        capture_exception(e)
