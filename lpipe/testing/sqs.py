"""
Example Usage

```python
@pytest.fixture(scope="session")
def sqs_queues():
    return ["TEST_SQS_QUEUE"]


@pytest.fixture(scope="class")
def sqs(localstack, sqs_queues):
    queue_urls = lpipe.testing.create_sqs_queues(sqs_queues, redrive=True)
    yield queue_urls
    lpipe.testing.destroy_sqs_queues(queue_urls)
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
def create_sqs_queue(q, dlq_url=None):
    client = boto3.client("sqs")
    attrs = {}
    if dlq_url:
        attrs["RedrivePolicy"] = json.dumps(
            {"deadLetterTargetArn": sqs.get_queue_arn(dlq_url), "maxReceiveCount": 1}
        )
    resp = utils.call(client.create_queue, QueueName=q, Attributes=attrs)["QueueUrl"]
    while not _sqs_queue_exists(q):
        sleep(1)
    return resp


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
    return utils.call(boto3.client("sqs").delete_queue, QueueUrl=url)


def destroy_sqs_queues(queues: dict):
    return {name: destroy_sqs_queue(url) for name, url in queues.items()}
