import json

from lpipe import kinesis


def test_kinesis_hash():
    hash = kinesis.hash(json.dumps({"foo": "bar"}, sort_keys=True))
    assert isinstance(hash, str) == True and len(hash) > 0
