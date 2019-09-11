import pytest

from lpipe.sqs import build


class TestBuild:
    def test_build(self):
        result = build(message_data={"foo": "bar"})
        assert result["MessageBody"] == '{"foo": "bar"}'

    def test_build_with_group_id(self):
        result = build(message_data={"foo": "bar"}, message_group_id=10)
        assert result["MessageBody"] == '{"foo": "bar"}'
        assert result["MessageGroupId"] == "10"
