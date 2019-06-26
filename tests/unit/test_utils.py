import json

from lpipe import utils


def test_kinesis_hash():
    hash = utils.hash(json.dumps({"foo": "bar"}, sort_keys=True))
    assert isinstance(hash, str) == True and len(hash) > 0


def test_batch():
    things = [1, 2, 3, 4, 5, 6]
    iter = list(utils.batch(things, 2))
    assert len(iter) == 3
    assert iter[0] == [1, 2]
    assert iter[1] == [3, 4]
    assert iter[2] == [5, 6]
