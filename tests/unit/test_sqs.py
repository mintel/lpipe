import pytest

from lpipe.sqs import build


# @pytest.mark.parametrize(
#     ["message", "message_group_id", "expected"],
#     [
#         (
#             {"a": "b"},
#             None,
#             {
#                 "Id": "f0c7f54eccba022bfc32fbc01bd8806d91569026",
#                 "MessageBody": '{"a": "b"}',
#             },
#         ),
#         (
#             {"a": "b"},
#             "10",
#             {
#                 "Id": "f0c7f54eccba022bfc32fbc01bd8806d91569026",
#                 "MessageGroupId": "10",
#                 "MessageBody": '{"a": "b"}',
#             },
#         ),
#     ],
# )
# def test_build(message, message_group_id, expected):
#     actual = build(message, message_group_id)
#     assert expected == actual


class TestBuild:
    def test_build(self):
        assert build(message_data={"foo": "bar"}) == {
            "Id": "bc4919c6adf7168088eaea06e27a5b23f0f9f9da",
            "MessageBody": '{"foo": "bar"}',
        }

    def test_build_with_group_id(self):
        assert build(message_data={"foo": "bar"}, message_group_id=10) == {
            "Id": "bc4919c6adf7168088eaea06e27a5b23f0f9f9da",
            "MessageGroupId": "10",
            "MessageBody": '{"foo": "bar"}',
        }
