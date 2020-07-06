import pytest

from lpipe.contrib import mindictive


class TestDictHelpers:
    @pytest.mark.parametrize(
        "fixture_name,fixture",
        [
            (
                "baseline",
                {
                    "obj": {"a": {"b": "testval"}},
                    "kwargs": {"keys": ["a", "b"]},
                    "output": "testval",
                    "type": str,
                },
            ),
            (
                "with_default",
                {
                    "obj": {"a": {"b": "testval"}},
                    "kwargs": {"keys": ["a", "b"], "default": "foobar"},
                    "output": "testval",
                    "type": str,
                },
            ),
            (
                "value_evals_false_with_none_default",
                {
                    "obj": {"a": {"b": {}}},
                    "kwargs": {"keys": ["a", "b"], "default": None},
                    "output": {},
                    "type": dict,
                },
            ),
            (
                "bad_with_default",
                {
                    "obj": {"a": {"b": "testval"}},
                    "kwargs": {"keys": ["a", "b", "c"], "default": "foobar"},
                    "output": "foobar",
                    "type": str,
                },
            ),
            (
                "bad_with_default_none",
                {
                    "obj": {"a": {"b": "testval"}},
                    "kwargs": {"keys": ["a", "b", "c"], "default": None},
                    "output": None,
                },
            ),
            (
                "bad_with_default_dict",
                {
                    "obj": {"a": {"b": "testval"}},
                    "kwargs": {"keys": ["a", "b", "c"], "default": {}},
                    "output": {},
                    "type": dict,
                },
            ),
            (
                "bad_with_default_list",
                {
                    "obj": {"a": {"b": "testval"}},
                    "kwargs": {"keys": ["a", "b", "c"], "default": []},
                    "output": [],
                    "type": list,
                },
            ),
        ],
    )
    def test_get(self, fixture_name, fixture):
        val = mindictive.get_nested(fixture["obj"], **fixture["kwargs"])
        if "type" in fixture:
            assert isinstance(val, fixture["type"])
        assert val == fixture["output"]

    @pytest.mark.parametrize(
        "fixture_name,fixture",
        [
            (
                "baseline",
                {
                    "obj": {"a": {"b": "testval"}},
                    "kwargs": {"keys": ["a", "b", "c"]},
                    "raises": KeyError,
                },
            )
        ],
    )
    def test_get_raises(self, fixture_name, fixture):
        with pytest.raises(fixture["raises"]):
            mindictive.get_nested(fixture["obj"], **fixture["kwargs"])


def test_set_nestesd():
    my_dict = {}
    mindictive.set_nested(my_dict, ["a", "b"], "testval")
    assert my_dict["a"]["b"] == "testval"
