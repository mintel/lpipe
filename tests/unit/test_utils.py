import json
from enum import Enum, EnumMeta

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


class FakePath(Enum):
    FOO = 1


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("enum", {"e": FakePath, "k": FakePath.FOO}),
        ("string", {"e": FakePath, "k": "FOO"}),
        ("string_lower", {"e": FakePath, "k": "foo"}),
        ("enum_cast_to_string", {"e": FakePath, "k": "FakePath.FOO"}),
    ],
)
def test_get_enum_value(fixture_name, fixture):
    assert utils.get_enum_value(**fixture) == FakePath.FOO


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


class TestGenerateEnum:
    def test_default(self):
        d = {"foo": "bar", "wiz": "bang"}
        output = utils.generate_enum(d)
        assert isinstance(output, EnumMeta)
        for k in d.keys():
            assert utils.get_enum_value(output, k)

    def test_bad_int(self):
        # You can't have an Enum with ints for names.
        d = {1: "bar", 2: "bang"}
        with pytest.raises(AttributeError):
            utils.generate_enum(d)


class TestAutoEncoder:
    def test_enum(self):
        AutoEnum = Enum("Auto", ["FOO", "BAR"])
        data = {AutoEnum.FOO: "wizbang"}
        encoded = json.dumps(
            {str(k): v for k, v in data.items()}, cls=utils.AutoEncoder
        )
        decoded = {
            utils.get_enum_value(AutoEnum, k): v for k, v in json.loads(encoded).items()
        }
        assert data == decoded

    def test_enum_as_key(self):
        FakePath = Enum("Auto", ["FOO", "BAR"])
        data = {FakePath.FOO: "wizbang"}
        with pytest.raises(TypeError):
            # python's json module WILL NOT encode dicts with non-str keys
            json.dumps(data, cls=utils.AutoEncoder)

    def test_bytes(self):
        data = {"foo": b"bar"}
        encoded = json.dumps(data, cls=utils.AutoEncoder)
        decoded = json.loads(encoded)
        assert decoded == {"foo": "bar"}

    def test_obj_json(self):
        class TestObj:
            def __init__(self, first, last):
                self.first = first
                self.last = last

            def _json(self):
                return f"{self.first} {self.last}"

        data = {"foo": TestObj("John", "Doe")}
        encoded = json.dumps(data, cls=utils.AutoEncoder)
        decoded = json.loads(encoded)
        assert decoded == {"foo": "John Doe"}

    def test_default(self):
        class TestObj:
            pass

        data = {"foo": TestObj()}
        with pytest.raises(TypeError):
            # Just checking that the default json encoder is called
            json.dumps(data, cls=utils.AutoEncoder)
