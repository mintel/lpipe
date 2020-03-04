import json

import boto3
import pytest

from lpipe import sqs, testing, utils


@pytest.mark.postbuild
@pytest.mark.usefixtures("kinesis")
def test_kinesis_fixtures(kinesis_streams):
    client = boto3.client("kinesis")
    client.put_record(
        StreamName=kinesis_streams[0],
        Data=json.dumps({"foo": "bar"}),
        PartitionKey="foobar",
    )


@pytest.mark.postbuild
@pytest.mark.usefixtures("sqs")
def test_sqs_fixtures(sqs_queues):
    queue_url = sqs.get_queue_url(sqs_queues[0])
    client = boto3.client("sqs")
    client.send_message(QueueUrl=queue_url, MessageBody=json.dumps({"foo": "bar"}))


@pytest.mark.postbuild
@pytest.mark.usefixtures("dynamodb")
def test_dynamodb_fixtures(dynamodb_tables):
    client = boto3.client("dynamodb")
    utils.call(testing.backoff_check, func=lambda: client.list_tables())
    for table in dynamodb_tables:
        response = utils.call(client.describe_table, TableName=table["TableName"])
        assert response["Table"]["TableName"] == table["TableName"]
