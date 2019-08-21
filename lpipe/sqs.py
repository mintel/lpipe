import json
import logging
from functools import wraps

import boto3
import botocore
from decouple import config

from lpipe.utils import batch, hash


def build(r):
    data = json.dumps(r, sort_keys=True)
    return {"Id": hash(data), "MessageBody": data}


def mock_sqs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (
            botocore.exceptions.NoCredentialsError,
            botocore.exceptions.ClientError,
            botocore.exceptions.NoRegionError,
        ):
            if config("MOCK_AWS", default=False):
                log.debug("{}({}, {})".format(func, args, kwargs))
                return
            else:
                raise

    return wrapper


@mock_sqs
def batch_put_messages(queue_url, messages, batch_size=10, **kwargs):
    """Put messages into a sqs queue, batched by the maximum of 10."""
    assert batch_size <= 10  # send_message_batch will fail otherwise
    client = boto3.client("sqs")
    responses = []
    for b in batch(messages, batch_size):
        response = client.send_message_batch(
            QueueUrl=queue_url, Entries=[build(message) for message in b]
        )
        responses.append(response)
    return tuple(responses)


def put_message(queue_url, message, **kwargs):
    return batch_put_messages(queue_url=queue_url, messages=[message])


@mock_sqs
def get_queue_url(queue_name):
    client = boto3.client("sqs")
    response = client.get_queue_url(QueueName=queue_name)
    return response["QueueUrl"]
