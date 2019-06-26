import boto3
import pytest

from lpipe import sqs


@pytest.mark.postbuild
@pytest.mark.usefixtures("localstack", "sqs")
class TestPutMessages:
    def test_batch_put_messages_single(self, sqs_queues):
        client = boto3.client("sqs")
        queue_url = sqs.get_queue_url(sqs_queues[0])
        responses = sqs.batch_put_messages(
            queue_url=queue_url,
            messages=[{"foo": "bar", "wiz": "bang"}],
            batch_size=2,
        )
        assert len(responses) == 1
        assert (
            all([r["ResponseMetadata"]["HTTPStatusCode"] == 200 for r in responses])
            == True
        )

    def test_batch_put_messages_many(self, sqs_queues):
        client = boto3.client("sqs")
        queue_url = sqs.get_queue_url(sqs_queues[0])
        responses = sqs.batch_put_messages(
            queue_url=queue_url,
            messages=[
                {"foo": "bar", "wiz": "bang"},
                {"lorem": "ipsum", "quid": "est"},
                {"foo": "bar", "wiz": "bang"},
                {"lorem": "ipsum", "quid": "est"},
            ],
            batch_size=2,
        )
        assert len(responses) == 2
        assert (
            all([r["ResponseMetadata"]["HTTPStatusCode"] == 200 for r in responses])
            == True
        )

    def test_batch_put_message(self, sqs_queues):
        client = boto3.client("sqs")
        queue_url = sqs.get_queue_url(sqs_queues[0])
        responses = sqs.put_message(
            queue_url=queue_url, message={"foo": "bar", "wiz": "bang"}
        )
        assert len(responses) == 1
        assert (
            all([r["ResponseMetadata"]["HTTPStatusCode"] == 200 for r in responses])
            == True
        )
