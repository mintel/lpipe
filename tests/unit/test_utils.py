import json
from enum import Enum

import pytest

from lpipe import exceptions, utils


def test_kinesis_hash():
    hash = utils.hash(json.dumps({"foo": "bar"}, sort_keys=True))
    assert isinstance(hash, str) and len(hash) > 0


def test_batch():
    things = [1, 2, 3, 4, 5, 6]
    iter = list(utils.batch(things, 2))
    assert len(iter) == 3
    assert iter[0] == [1, 2]
    assert iter[1] == [3, 4]
    assert iter[2] == [5, 6]


class TestDictHelpers:
    def test_get(self):
        my_dict = {"a": {"b": "testval"}}
        assert utils.get_nested(my_dict, ["a", "b"]) == "testval"

    def test_get_bad(self):
        with pytest.raises(KeyError):
            my_dict = {"a": {"b": "testval"}}
            utils.get_nested(my_dict, ["a", "b", "c"])

    def test_get_with_default(self):
        my_dict = {"a": {"b": "testval"}}
        assert utils.get_nested(my_dict, ["a", "b"], "foobar") == "testval"

    def test_get_bad_with_default(self):
        my_dict = {"a": {"b": "testval"}}
        assert utils.get_nested(my_dict, ["a", "b", "c"], "foobar") == "foobar"

    def test_get_bad_with_default_none(self):
        my_dict = {"a": {"b": "testval"}}
        assert not utils.get_nested(my_dict, ["a", "b", "c"], None)

    def test_set(self):
        my_dict = {}
        utils.set_nested(my_dict, ["a", "b"], "testval")
        assert my_dict["a"]["b"] == "testval"

    def test_get_falsy(self):
        my_dict = {"a": {"b": 0}}
        assert utils.get_nested(my_dict, ["a", "b"], None) == 0


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


@pytest.mark.parametrize(
    "fixture_name,fixture,raises",
    [
        ("string", "BAD", exceptions.InvalidPathError),
        ("enum_cast_to_string", "TestPath.BAD", exceptions.InvalidPathError),
    ],
)
def test_get_bad_enum_value(fixture_name, fixture, raises):
    path_enum = Enum("TestPath", ["FOO", "BAR"])
    with pytest.raises(raises):
        utils.get_enum_value(e=path_enum, k=fixture)
