from lpipe.pipeline import (
    get_kinesis_payload,
    get_payload_from_record,
    get_records_from_event,
    get_sqs_payload,
    QueueType,
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
