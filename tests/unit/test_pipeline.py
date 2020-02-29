import pytest

from lpipe.pipeline import (
    QueueType,
    get_kinesis_payload,
    get_payload_from_record,
    get_records_from_event,
    get_sqs_payload,
    validate_signature,
)


def test_kinesis_payload(kinesis_payload):
    records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
    payload = kinesis_payload(records)
    assert "Records" in payload
    decoded_records = [get_kinesis_payload(r) for r in payload["Records"]]
    for r in decoded_records:
        assert "path" in r
        assert r["path"] == "foo"
        assert "kwargs" in r
        assert isinstance(r["kwargs"], dict)


def test_sqs_payload(sqs_payload):
    records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
    payload = sqs_payload(records)
    assert "Records" in payload
    decoded_records = [get_sqs_payload(r) for r in payload["Records"]]
    for r in decoded_records:
        assert "path" in r
        assert r["path"] == "foo"
        assert "kwargs" in r
        assert isinstance(r["kwargs"], dict)


class TestGetRecordsFromEvent:
    def test_kinesis(self, kinesis_payload):
        records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
        payload = kinesis_payload(records)
        records = get_records_from_event(QueueType.KINESIS, payload)
        assert len(records) == 2

    def test_sqs(self, sqs_payload):
        records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
        payload = sqs_payload(records)
        records = get_records_from_event(QueueType.SQS, payload)
        assert len(records) == 2


class TestGetPayloadFromRecord:
    def test_kinesis(self, kinesis_payload):
        records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
        payload = kinesis_payload(records)
        records = get_records_from_event(QueueType.KINESIS, payload)
        for r in records:
            record = get_payload_from_record(QueueType.KINESIS, r)
            assert "path" in record and record["path"] == "foo"

    def test_sqs(self, sqs_payload):
        records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
        payload = sqs_payload(records)
        records = get_records_from_event(QueueType.SQS, payload)
        for r in records:
            record = get_payload_from_record(QueueType.SQS, r)
            assert "path" in record and record["path"] == "foo"


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
