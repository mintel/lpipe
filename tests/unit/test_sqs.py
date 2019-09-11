import pytest

from lpipe.sqs import build


@pytest.mark.parametrize(
    ["message", "message_group_id", "expected"],
    [
        (
            {"a": "b"},
            None,
            {
                "Id": "f0c7f54eccba022bfc32fbc01bd8806d91569026",
                "MessageBody": '{"a": "b"}',
            },
        ),
        (
            {"a": "b"},
            "10",
            {
                "Id": "f0c7f54eccba022bfc32fbc01bd8806d91569026",
                "MessageGroupId": "10",
                "MessageBody": '{"a": "b"}',
            },
        ),
    ],
)
def test_build(message, message_group_id, expected):
    actual = build(message, message_group_id)
    assert expected == actual
