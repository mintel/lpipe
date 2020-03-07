import boto3
import pytest
from botocore.exceptions import ClientError

from lpipe import sqs, testing
from lpipe.utils import check_status, set_env


def test_mock(environment):
    with set_env(environment(MOCK_AWS=True)):
        sqs.put_message("foobar", {"foo": "bar"})


class TestBuild:
    def test_build(self):
        result = sqs.build(message_data={"foo": "bar"})
        assert result["MessageBody"] == '{"foo": "bar"}'

    def test_build_with_group_id(self):
        result = sqs.build(message_data={"foo": "bar"}, message_group_id=10)
        assert result["MessageBody"] == '{"foo": "bar"}'
        assert result["MessageGroupId"] == "10"


@pytest.mark.usefixtures("sqs_moto")
class TestPutMessages:
    def test_batch_put_messages_single(self, sqs_queues):
        client = boto3.client("sqs")
        queue_url = sqs.get_queue_url(sqs_queues[0])
        responses = sqs.batch_put_messages(
            queue_url=queue_url, messages=[{"foo": "bar", "wiz": "bang"}], batch_size=2
        )
        assert len(responses) == 1
        assert all([check_status(r) for r in responses]) == True

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
        assert all([check_status(r) for r in responses]) == True

    def test_batch_put_message(self, sqs_queues):
        client = boto3.client("sqs")
        queue_url = sqs.get_queue_url(sqs_queues[0])
        responses = sqs.put_message(
            queue_url=queue_url, data={"foo": "bar", "wiz": "bang"}
        )
        assert len(responses) == 1
        assert all([check_status(r) for r in responses]) == True
