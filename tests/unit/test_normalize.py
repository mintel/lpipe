import pytest
from enum import Enum, EnumMeta
from typing import Callable

import lpipe
import lpipe.exceptions
from lpipe import action, normalize, queue, utils

fake_enum = Enum("Auto", ["FOO", "BAR"])
fake_queue = queue.Queue(type=queue.QueueType.SQS, name="foobar", path="wizbang")


def generic_test(fixture: dict, callable: Callable):
    def check(f):
        assert callable(**f["input"]) == f["output"]

    if fixture.get("raises", None):
        with pytest.raises(fixture["raises"]):
            check(fixture)
    else:
        check(fixture)


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        (
            "queue",
            {
                "input": {"path_enum": fake_enum, "path": fake_queue},
                "output": fake_queue,
                "raises": None,
            },
        ),
        (
            "enum",
            {
                "input": {"path_enum": fake_enum, "path": fake_enum.FOO},
                "output": fake_enum.FOO,
                "raises": None,
            },
        ),
        (
            "str",
            {
                "input": {"path_enum": fake_enum, "path": "FOO"},
                "output": fake_enum.FOO,
                "raises": None,
            },
        ),
        (
            "long_str",
            {
                "input": {"path_enum": fake_enum, "path": "Auto.FOO"},
                "output": fake_enum.FOO,
                "raises": None,
            },
        ),
        (
            "bad_str",
            {
                "input": {"path_enum": fake_enum, "path": "WIZBANG"},
                "output": None,
                "raises": lpipe.exceptions.InvalidPathError,
            },
        ),
    ],
)
def test_normalize_path(fixture_name, fixture):
    generic_test(fixture, normalize.normalize_path)


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        (
            "enum_str",
            {
                "input": {
                    "path_enum": fake_enum,
                    "paths": {fake_enum.FOO: None, "BAR": None},
                },
                "output": {fake_enum.FOO: None, fake_enum.BAR: None},
            },
        )
    ],
)
def test_normalize_paths(fixture_name, fixture):
    generic_test(fixture, normalize.normalize_paths)


class TestNormalizeActions:
    def test_functions(self):
        fake_func = lambda x: None
        fake_func2 = lambda y: None
        funcs = [fake_func, fake_func2]
        output = normalize.normalize_actions(funcs)
        assert isinstance(output, list)
        assert isinstance(output[0], action.Action)
        assert output[0].functions == funcs

    def test_actions(self):
        fake_func = lambda x: None
        fake_func2 = lambda y: None
        actions = [action.Action(paths=["FOO"]), action.Action(paths=["BAR"])]
        output = normalize.normalize_actions(actions)
        assert output == actions


class TestNormalizePathEnum:
    def test_default(self):
        path_enum = fake_enum
        paths = {fake_enum.FOO: None, "BAR": None}
        assert normalize.normalize_path_enum(paths=paths, path_enum=path_enum) == (
            paths,
            path_enum,
        )

    def test_no_enum(self):
        _path_enum = None
        _paths = {"FOO": None, "BAR": None}
        paths, path_enum = normalize.normalize_path_enum(
            paths=_paths, path_enum=_path_enum
        )
        for k in paths.keys():
            assert isinstance(k, path_enum)
