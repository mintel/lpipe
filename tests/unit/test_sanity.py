import json

import boto3
import pytest

from lpipe import sqs, testing, utils


def test_sanity():
    pass


def test_sqs_moto_fixtures(sqs_queues, sqs_moto):
    for q in sqs_queues:
        queue_url = sqs.get_queue_url(q)
        client = boto3.client("sqs")
        utils.call(
            client.send_message,
            QueueUrl=queue_url,
            MessageBody=json.dumps({"foo": "bar"}),
        )
