import json
import logging
from functools import wraps

import boto3
import botocore
from decouple import config

from lpipe.utils import batch, hash


def build(message_data, message_group_id):
    data = json.dumps(message_data, sort_keys=True)
    message = {"Id": hash(data), "MessageBody": data}
    if message_group_id:
        message["MessageGroupId"] = message_group_id
    return message


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
                log = kwargs["logger"] if "logger" in kwargs else logging.getLogger()
                log.debug(
                    "Mocked SQS: {}()".format(func),
                    function=f"{func}",
                    params={"args": f"{args}", "kwargs": f"{kwargs}"},
                )
                return
            else:
                raise

    return wrapper


@mock_sqs
def batch_put_messages(
    queue_url, messages, batch_size=10, message_group_id=None, **kwargs
):
    """Put messages into a sqs queue, batched by the maximum of 10."""
    assert batch_size <= 10  # send_message_batch will fail otherwise
    client = boto3.client("sqs")
    responses = []
    for b in batch(messages, batch_size):
        response = client.send_message_batch(
            QueueUrl=queue_url,
            Entries=[build(message, message_group_id) for message in b],
        )
        responses.append(response)
    return tuple(responses)


def put_message(queue_url, data, **kwargs):
    return batch_put_messages(queue_url=queue_url, messages=[data])


@mock_sqs
def get_queue_url(queue_name):
    client = boto3.client("sqs")
    response = client.get_queue_url(QueueName=queue_name)
    return response["QueueUrl"]
