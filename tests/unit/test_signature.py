import pytest

from lpipe import signature


class TestMerge:
    def test_merge(self):
        def f1(a: int, b: dict):
            pass

        def f2(a: int, c: str, d: list):
            pass

        output = signature._merge_signatures([f1, f2])
        print(f"{output}")

    def test_merge_param_clash(self):
        def f1(a: int, b: dict):
            pass

        def f2(a: str):
            pass

        with pytest.raises(TypeError):
            signature._merge_signatures([f1, f2])


class TestValidateSignature:
    def test_no_hints(self):
        def _test_func(a, b, c, **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": 3}
        validated_params = signature.validate([_test_func], params)
        assert validated_params == {"a": 1, "b": 2, "c": 3}

    def test_no_hints_raises(self):
        def _test_func(a, b, c, **kwargs):
            pass

        params = {"b": 2, "c": 3}
        with pytest.raises(TypeError):
            signature.validate([_test_func], params)

    def test_mixed_hints(self):
        def _test_func(a: str, b, c, **kwargs):
            pass

        params = {"a": "foo", "b": 2, "c": 3}
        validated_params = signature.validate([_test_func], params)
        assert validated_params == {"a": "foo", "b": 2, "c": 3}

    def test_mixed_hints_raises(self):
        def _test_func(a: str, b, c, **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": 3}
        with pytest.raises(TypeError):
            signature.validate([_test_func], params)

    def test_hints_defaults(self):
        def _test_func(a, b, c: str = "asdf", **kwargs):
            pass

        params = {"a": 1, "b": 2}
        validated_params = signature.validate([_test_func], params)
        assert validated_params == {"a": 1, "b": 2}

    def test_hints_defaults_override(self):
        def _test_func(a, b, c: str = "asdf", **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": "foobar"}
        validated_params = signature.validate([_test_func], params)
        assert validated_params == {"a": 1, "b": 2, "c": "foobar"}

    def test_hint_with_none_default(self):
        def _test_func(a, b, c: str = None, **kwargs):
            pass

        params = {"a": 1, "b": 2}
        validated_params = signature.validate([_test_func], params)
        assert validated_params == {"a": 1, "b": 2}

    def test_hint_with_none_default_but_set(self):
        def _test_func(a, b, c: str = None, **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": "foobar"}
        validated_params = signature.validate([_test_func], params)
        assert validated_params == {"a": 1, "b": 2, "c": "foobar"}

    def test_hint_with_none_default_raises(self):
        def _test_func(a, b, c: str = None, **kwargs):
            pass

        params = {"a": 1, "b": 2, "c": 3}
        with pytest.raises(TypeError):
            signature.validate([_test_func], params)
