from lpipe import pipeline


def test_kinesis_payload(kinesis_payload):
    records = [{"path": "foo", "kwargs": {}}, {"path": "foo", "kwargs": {}}]
    payload = kinesis_payload(records)
    assert "Records" in payload
    decoded_records = [pipeline.get_kinesis_payload(r) for r in payload["Records"]]
    for r in decoded_records:
        assert "path" in r
        assert r["path"] == "foo"
        assert "kwargs" in r
        assert isinstance(r["kwargs"], dict)


def test_sqs_payload(sqs_payload):
    pass
