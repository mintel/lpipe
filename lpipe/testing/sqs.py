"""
Example Usage

```python
@pytest.fixture(scope="session")
def sqs_queues():
    return ["TEST_SQS_QUEUE"]


@pytest.fixture(scope="class")
def sqs(localstack, sqs_queues):
    yield lpipe.testing.create_sqs_queues(sqs_queues)
    lpipe.testing.destroy_sqs_queues(sqs_queues)
```
"""

import json
from time import sleep

import backoff
import boto3
from botocore.exceptions import ClientError

from .. import exceptions, sqs, utils


def sqs_payload(payloads):
    def fmt(p):
        return {"body": json.dumps(p)}

    records = [fmt(p) for p in payloads]
    return {"Records": records}


def _sqs_queue_exists(q):
    try:
        sqs.get_queue_url(q)
        return True
    except:
        return False


@backoff.on_exception(backoff.expo, ClientError, max_time=30)
def create_sqs_queue(q):
    resp = utils.call(boto3.client("sqs").create_queue, QueueName=q)["QueueUrl"]
    while not _sqs_queue_exists(q):
        sleep(1)
    return resp


def create_sqs_queues(names: list):
    return {n: create_sqs_queue(n) for n in names}


@backoff.on_exception(backoff.expo, ClientError, max_tries=3)
def destroy_sqs_queue(q):
    return utils.call(boto3.client("sqs").delete_queue, QueueUrl=sqs.get_queue_url(q))


def destroy_sqs_queues(names: list):
    return {n: destroy_sqs_queue(n) for n in names}
