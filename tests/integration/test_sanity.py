import json

import pytest
import boto3

KINESIS_STREAMS = ["test_stream"]


@pytest.mark.postbuild
@pytest.mark.usefixtures("kinesis")
class TestSanityMockKinesis:
    def test_mock_kinesis(self, kinesis_streams):
        client = boto3.client("kinesis")
        client.put_record(
            StreamName=kinesis_streams[0],
            Data=json.dumps({"foo": "bar"}),
            PartitionKey="foobar",
        )


# class TestSanityMockSQS:
#    test_mock_sqs(self):
