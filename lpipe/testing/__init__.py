import json
import logging

from .awslambda import *
from .dynamodb import *
from .kinesis import *
from .sqs import *


@backoff.on_exception(backoff.expo, (TimeoutError, ClientError), max_time=30)
def backoff_check(func):
    return func()


def raw_payload(payloads):
    def fmt(p):
        return json.dumps(p).encode()

    records = [fmt(p) for p in payloads]
    return records


def environment(
    fixtures: dict = {},
    sqs_queues: list = [],
    kinesis_streams: list = [],
    dynamodb_tables: list = [],
):
    def clean(s):
        return s.upper().replace("-", "_")

    def env(**kwargs):
        vars = {
            "APP_ENVIRONMENT": "localstack",
            "SENTRY_DSN": "https://public:private@sentry.localhost:1234/1",
            "AWS_DEFAULT_REGION": "us-east-2",
        }
        vars.update(fixtures)
        vars.update({clean(s): s for s in kinesis_streams})
        vars.update({clean(q): q for q in sqs_queues})
        vars.update({clean(t["TableName"]): t["TableName"] for t in dynamodb_tables})
        will_overwrite = list(set(vars.keys()) & set(kwargs.keys()))
        if will_overwrite:
            logging.getLogger().warn(
                f"Your tests are going to overwrite the following fields: {will_overwrite}"
            )
        vars.update(kwargs)
        return vars

    return env
