from contextlib import contextmanager
from functools import wraps

from decouple import config

try:
    import sentry_sdk
    from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
except ImportError:
    raise Exception(
        "lpipe.contrib.sentry requires the sentry_sdk package, please install it to proceed"
    )


def _set_tags(scope, context):
    for k, v in context.items():
        scope.set_tag(k, v)


def init(dsn: str = None, context: dict = None):
    if not dsn:
        dsn = config("SENTRY_DSN")
    sentry_sdk.init(dsn=dsn, integrations=[AwsLambdaIntegration()])
    if context:
        with sentry_sdk.configure_scope() as scope:
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
        with sentry_sdk.push_scope() as scope:
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
        sentry_sdk.capture_exception(e)
