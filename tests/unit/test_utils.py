import json
from enum import Enum

import pytest

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


def test_dict_helpers():
    my_dict = {}

    utils.set_nested(my_dict, ["a", "b", "c", "wiz", "bang"], "test1")
    assert my_dict == {"a": {"b": {"c": {"wiz": {"bang": "test1"}}}}}

    val = utils.get_nested(my_dict, ["a", "b", "c", "wiz", "bang"])
    assert val == "test1"

    utils.set_nested(my_dict, ["a", "b", "c", "wiz", "bang"], "test2")
    assert my_dict == {"a": {"b": {"c": {"wiz": {"bang": "test2"}}}}}

    val = utils.get_nested(my_dict, ["a", "b", "c", "wiz", "bang"])
    assert val == "test2"


class Path(Enum):
    FOO = 1


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("enum", {"e": Path, "k": Path.FOO}),
        ("string", {"e": Path, "k": "FOO"}),
        ("enum_cast_to_string", {"e": Path, "k": "Path.FOO"}),
    ],
)
def test_get_enum_value(fixture_name, fixture):
    assert utils.get_enum_value(**fixture) == Path.FOO
