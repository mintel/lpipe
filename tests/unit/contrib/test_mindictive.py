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
