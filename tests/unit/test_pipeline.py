from enum import Enum

import pytest

from lpipe.pipeline import (
    Payload,
    Queue,
    QueueType,
    get_kinesis_payload,
    get_payload_from_record,
    get_raw_payload,
    get_records_from_event,
    get_sqs_payload,
    validate_signature,
)
from lpipe.testing import kinesis_payload, raw_payload, sqs_payload


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("sqs", {"encode_func": sqs_payload, "decode_func": get_sqs_payload}),
        (
            "kinesis",
            {"encode_func": kinesis_payload, "decode_func": get_kinesis_payload},
        ),
    ],
)
def test_encode_payload(fixture_name, fixture):
    records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
    payload = fixture["encode_func"](records)
    assert "Records" in payload
    decoded_records = [fixture["decode_func"](r) for r in payload["Records"]]
    for r in decoded_records:
        assert "path" in r
        assert r["path"] == "foo"
        assert "kwargs" in r
        assert isinstance(r["kwargs"], dict)


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("sqs", {"encode_func": sqs_payload, "queue_type": QueueType.SQS}),
        ("kinesis", {"encode_func": kinesis_payload, "queue_type": QueueType.KINESIS}),
        ("raw", {"encode_func": raw_payload, "queue_type": QueueType.RAW}),
    ],
)
def test_get_records_from_event(fixture_name, fixture):
    records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
    payload = fixture["encode_func"](records)
    event_records = get_records_from_event(fixture["queue_type"], payload)
    assert len(records) == len(event_records)


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("sqs", {"encode_func": sqs_payload, "queue_type": QueueType.SQS}),
        ("kinesis", {"encode_func": kinesis_payload, "queue_type": QueueType.KINESIS}),
        ("raw", {"encode_func": raw_payload, "queue_type": QueueType.RAW}),
    ],
)
def test_get_payload_from_record(fixture_name, fixture):
    records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
    payload = fixture["encode_func"](records)
    event_records = get_records_from_event(fixture["queue_type"], payload)
    payload_records = [
        get_payload_from_record(fixture["queue_type"], r) for r in event_records
    ]
    assert payload_records == records


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [("name", {"name": "foobar"}), ("url", {"url": "http://www.foo.com/bar"})],
)
def test_queue(fixture_name, fixture):
    q = Queue(QueueType.SQS, "FOO", **fixture)
    assert q


class Path(Enum):
    FOO = 1


class TestPayload:
    @pytest.mark.parametrize(
        "fixture_name,fixture",
        [
            ("enum", {"path": Path.FOO, "kwargs": {"foo": "bar"}}),
            ("string", {"path": "FOO", "kwargs": {"foo": "bar"}}),
            ("empty_kwargs", {"path": Path.FOO, "kwargs": {}}),
        ],
    )
    def test_payload(self, fixture_name, fixture):
        Payload(**fixture).validate(Path)

    @pytest.mark.parametrize(
        "fixture_name,fixture",
        [
            ("enum", {"type": QueueType.SQS, "path": Path.FOO, "name": "foobar"}),
            ("string", {"type": QueueType.SQS, "path": "FOO", "name": "foobar"}),
        ],
    )
    def test_queue_payload(self, fixture_name, fixture):
        q = Queue(**fixture)
        Payload(q, {"foo": "bar"}).validate()


class TestValidateSignature:
    def test_no_hints(self):
        def _test_func(a, b, c, **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": 3}
        validated_params = validate_signature([_test_func], params)
        assert validated_params == {"a": 1, "b": 2, "c": 3}

    def test_no_hints_raises(self):
        def _test_func(a, b, c, **kwargs):
            pass

        params = {"b": 2, "c": 3}
        with pytest.raises(TypeError):
            validate_signature([_test_func], params)

    def test_mixed_hints(self):
        def _test_func(a: str, b, c, **kwargs):
            pass

        params = {"a": "foo", "b": 2, "c": 3}
        validated_params = validate_signature([_test_func], params)
        assert validated_params == {"a": "foo", "b": 2, "c": 3}

    def test_mixed_hints_raises(self):
        def _test_func(a: str, b, c, **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": 3}
        with pytest.raises(TypeError):
            validate_signature([_test_func], params)

    def test_hints_defaults(self):
        def _test_func(a, b, c: str = "asdf", **kwargs):
            pass

        params = {"a": 1, "b": 2}
        validated_params = validate_signature([_test_func], params)
        assert validated_params == {"a": 1, "b": 2}

    def test_hints_defaults_override(self):
        def _test_func(a, b, c: str = "asdf", **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": "foobar"}
        validated_params = validate_signature([_test_func], params)
        assert validated_params == {"a": 1, "b": 2, "c": "foobar"}

    def test_hint_with_none_default(self):
        def _test_func(a, b, c: str = None, **kwargs):
            pass

        params = {"a": 1, "b": 2}
        validated_params = validate_signature([_test_func], params)
        assert validated_params == {"a": 1, "b": 2}

    def test_hint_with_none_default_but_set(self):
        def _test_func(a, b, c: str = None, **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": "foobar"}
        validated_params = validate_signature([_test_func], params)
        assert validated_params == {"a": 1, "b": 2, "c": "foobar"}

    def test_hint_with_none_default_raises(self):
        def _test_func(a, b, c: str = None, **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": 3}
        with pytest.raises(TypeError):
            validate_signature([_test_func], params)
