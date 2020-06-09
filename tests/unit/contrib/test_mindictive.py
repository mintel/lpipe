import pytest

from lpipe.contrib import mindictive


class TestDictHelpers:
    def test_get(self):
        my_dict = {"a": {"b": "testval"}}
        assert mindictive.get_nested(my_dict, ["a", "b"]) == "testval"

    def test_get_bad(self):
        with pytest.raises(KeyError):
            my_dict = {"a": {"b": "testval"}}
            mindictive.get_nested(my_dict, ["a", "b", "c"])

    def test_get_with_default(self):
        my_dict = {"a": {"b": "testval"}}
        assert mindictive.get_nested(my_dict, ["a", "b"], "foobar") == "testval"

    def test_get_bad_with_default(self):
        my_dict = {"a": {"b": "testval"}}
        assert mindictive.get_nested(my_dict, ["a", "b", "c"], "foobar") == "foobar"

    def test_get_bad_with_default_none(self):
        my_dict = {"a": {"b": "testval"}}
        assert not mindictive.get_nested(my_dict, ["a", "b", "c"], None)

    def test_set(self):
        my_dict = {}
        mindictive.set_nested(my_dict, ["a", "b"], "testval")
        assert my_dict["a"]["b"] == "testval"

    def test_get_object(self):
        class FooBar:
            def __init__(self, asdf):
                self.asdf = asdf

        my_dict = {"a": {"b": FooBar("testval")}}
        assert mindictive.get_nested(my_dict, ["a", "b", "asdf"]) == "testval"
        with pytest.raises(KeyError):
            mindictive.get_nested(my_dict, ["a", "b", "ghjk"])

    def test_get_object_with_default(self):
        class FooBar:
            def __init__(self, asdf):
                self.asdf = asdf

        my_dict = {"a": {"b": FooBar("testval")}}
        assert (
            mindictive.get_nested(my_dict, ["a", "b", "asdf"], "defaultval")
            == "testval"
        )
        assert (
            mindictive.get_nested(my_dict, ["a", "b", "ghjk"], "defaultval")
            == "defaultval"
        )
