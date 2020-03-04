"""
Example Usage

```python
@pytest.fixture(scope="session")
def sqs_queues():
    return ["TEST_SQS_QUEUE"]


@pytest.fixture(scope="class")
def sqs(localstack, sqs_queues):
    try:
        yield lpipe.testing.create_sqs_queues(sqs_queues)
    finally:
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


@backoff.on_exception(backoff.expo, ClientError, max_tries=3)
def create_sqs_queue(q):
    client = boto3.client("sqs")
    return utils.call(client.create_queue, QueueName=q)["QueueUrl"]


def create_sqs_queues(names: list):
    client = boto3.client("sqs")

    def queue_exists(q):
        try:
            sqs.get_queue_url(q)
            return True
        except:
            return False

    queues = {}

    for name in names:
        try:
            queues[name] = create_sqs_queue(name)
        except ClientError:
            exists = queue_exists(name)
            raise Exception(f"queue_exists({name}) -> {exists}") from e

    for name in names:
        while not queue_exists(name):
            sleep(1)

    return queues


@backoff.on_exception(backoff.expo, ClientError, max_tries=3)
def destroy_sqs_queue(q):
    client = boto3.client("sqs")
    return utils.call(client.delete_queue, QueueUrl=sqs.get_queue_url(q))


def destroy_sqs_queues(names: list):
    client = boto3.client("sqs")
    for name in names:
        try:
            destroy_sqs_queue(name)
        except ClientError as e:
            code = utils.describe_client_error(e)
            if code != "QueueDoesNotExist":
                raise TestingException("Queue does not exist.") from e
            raise
