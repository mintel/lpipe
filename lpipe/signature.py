import inspect
from types import FunctionType
from typing import Union, get_type_hints


def _merge(functions: list, iter):
    """Get a set of attributes describing several functions.

    Args:
        functions (list): list of functions (FunctionType)

    Raises:
        TypeError: If two functions have the same parameter name with different types or defaults.
    """
    output = {}
    for f in functions:
        assert isinstance(f, FunctionType)
        i = iter(f)
        for k, v in i.items():
            if k in output:
                try:
                    assert v == output[k]
                except AssertionError as e:
                    raise TypeError(
                        f"Incompatible functions {functions}: {k} represented as both {v} and {output[k]}"
                    ) from e
            else:
                output[k] = v
    return output


def _merge_signatures(functions: list):
    """Create a combined list of function parameters."""
    return _merge(functions, lambda f: inspect.signature(f).parameters)


def _merge_type_hints(functions: list):
    """Create a combined list of function parameter type hints."""
    return _merge(functions, lambda f: get_type_hints(f))


def _get_defaults(signature):
    """Create a dict of function parameters with defaults."""
    return {
        k: v.default
        for k, v in signature.items()
        if v.default is not inspect.Parameter.empty
    }


def validate(functions: list, params: dict) -> dict:
    """Validate and build kwargs for a set of functions based on their signatures.

    Args:
        functions (list): functions
        params (dict): kwargs provided in the event's message

    Returns:
        dict: validated kwargs required by the provided set of functions
    """
    signature = _merge_signatures(functions)
    defaults = _get_defaults(signature)
    hints = _merge_type_hints(functions)

    validated = {}
    for k, v in signature.items():
        if k in params:
            p = params[k]
            if k in hints:
                t = hints[k]
                try:
                    if hasattr(t, "__origin__") and t.__origin__ is Union:
                        # https://stackoverflow.com/a/49471187
                        assert any([isinstance(p, typ) for typ in t.__args__])
                    else:
                        assert isinstance(p, t)
                except AssertionError as e:
                    raise TypeError(f"Type of {k} should be {t} not {type(p)}.") from e
                validated[k] = p
            else:
                validated[k] = p
        elif k not in ("kwargs", "args"):
            try:
                assert k in defaults
            except AssertionError as e:
                raise TypeError(f"{functions} missing required argument: '{k}'") from e

    return validated
