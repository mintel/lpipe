import json

import boto3
import pytest

from lpipe import sqs


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "kinesis")
class TestSanityMockKinesis:
    def test_mock_kinesis(self, kinesis_streams):
        client = boto3.client("kinesis")
        client.put_record(
            StreamName=kinesis_streams[0],
            Data=json.dumps({"foo": "bar"}),
            PartitionKey="foobar",
        )


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "sqs")
class TestSanityMockSQS:
    def test_mock_sqs(self, sqs_queues):
        queue_url = sqs.get_queue_url(sqs_queues[0])
        client = boto3.client("sqs")
        client.send_message(QueueUrl=queue_url, MessageBody=json.dumps({"foo": "bar"}))
