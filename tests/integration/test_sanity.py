import json

import boto3
import pytest

from lpipe import sqs, testing, utils


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack")
class TestMockWithLocalstack:
    @pytest.mark.usefixtures("kinesis")
    def test_kinesis_fixtures(self, kinesis_streams):
        client = boto3.client("kinesis")
        for ks in kinesis_streams:
            client.put_record(
                StreamName=ks, Data=json.dumps({"foo": "bar"}), PartitionKey="foobar"
            )

    @pytest.mark.usefixtures("sqs")
    def test_sqs_fixtures(self, sqs_queues):
        client = boto3.client("sqs")
        for q in sqs_queues:
            queue_url = sqs.get_queue_url(q)
            utils.call(
                client.send_message,
                QueueUrl=queue_url,
                MessageBody=json.dumps({"foo": "bar"}),
            )

    @pytest.mark.usefixtures("dynamodb")
    def test_dynamodb_fixtures(self, dynamodb_tables):
        client = boto3.client("dynamodb")
        resp = utils.call(testing.backoff_check, func=lambda: client.list_tables())
        for table in dynamodb_tables:
            name = table["TableName"]
            assert name in resp["TableNames"]
