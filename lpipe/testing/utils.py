import json
import logging
from collections import namedtuple

import backoff
from botocore.exceptions import ClientError


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
    s3_buckets: list = [],
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
        vars.update({clean(q): q for q in s3_buckets})
        vars.update({clean(t["TableName"]): t["TableName"] for t in dynamodb_tables})
        will_overwrite = list(set(vars.keys()) & set(kwargs.keys()))
        if will_overwrite:
            logging.getLogger().warning(
                f"Your tests are going to overwrite the following fields: {will_overwrite}"
            )
        vars.update(kwargs)
        return vars

    return env


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


MockContext = namedtuple("Context", ["function_name"])
