"""
Example Usage

```python
@pytest.fixture(scope="session")
def sqs_queues():
    return ["TEST_SQS_QUEUE"]

@pytest.fixture(scope="class")
def sqs(localstack, sqs_queues):
    with lpipe.testing.setup_s3(s3_buckets) as buckets:
        yield buckets
```
"""

import json
import logging
from contextlib import contextmanager

import backoff
from botocore.exceptions import ClientError

from .. import _boto3, utils
from ..sqs import get_queue_arn, get_queue_url
from .utils import backoff_check


def sqs_payload(payloads):
    def fmt(p):
        return {"body": json.dumps(p)}

    records = [fmt(p) for p in payloads]
    return {"Records": records}


def _sqs_queue_exists(q):
    try:
        get_queue_url(q)
        return True
    except Exception:
        logging.getLogger().info(f"Queue {q} does not exist yet.")
        return False


@backoff.on_exception(backoff.expo, ClientError, max_time=30)
def create_sqs_queue(q, dlq_url=None):
    client = _boto3.client("sqs")
    attrs = {}
    if dlq_url:
        attrs["RedrivePolicy"] = json.dumps(
            {"deadLetterTargetArn": get_queue_arn(dlq_url), "maxReceiveCount": 1}
        )
    resp = utils.call(client.create_queue, QueueName=q, Attributes=attrs)
    utils.call(
        backoff_check, func=lambda: _boto3.client("sqs").get_queue_url(QueueName=q)
    )
    return resp["QueueUrl"]


def create_sqs_queues(names: list, redrive=False):
    resp = {}
    for n in names:
        if redrive:
            dlq_name = f"{n}-dlq"
            resp[dlq_name] = create_sqs_queue(dlq_name)
            resp[n] = create_sqs_queue(n, dlq_url=resp[dlq_name])
        else:
            resp[n] = create_sqs_queue(n)

    return resp


@backoff.on_exception(backoff.expo, ClientError, max_tries=3)
def destroy_sqs_queue(url):
    return utils.call(_boto3.client("sqs").delete_queue, QueueUrl=url)


def destroy_sqs_queues(queues: dict):
    return {name: destroy_sqs_queue(url) for name, url in queues.items()}


@contextmanager
def setup_sqs(names, redrive=False):
    queues = create_sqs_queues(names, redrive=redrive)
    try:
        yield queues
    finally:
        destroy_sqs_queues(queues)
