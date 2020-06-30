from enum import Enum, EnumMeta
from types import FunctionType
from typing import List, Union

import lpipe.exceptions
from lpipe import action, utils


def normalize_path(path_enum: EnumMeta, path: Union[str, Enum]) -> Enum:
    try:
        return utils.get_enum_value(path_enum, path)
    except Exception as e:
        raise lpipe.exceptions.InvalidPathError(
            "Unable to cast your path identifier to an enum."
        ) from e


def normalize_paths(path_enum: EnumMeta, paths: dict) -> dict:
    return {normalize_path(path_enum, k): v for k, v in paths.items()}


def normalize_actions(
    actions: List[Union[FunctionType, action.Action]]
) -> List[action.Action]:
    """Normalize a path definition to a list of Action objects

    Args:
        actions (list): a list of FunctionType or Action objects

    Returns:
        list: a list of Action objects
    """
    # Allow someone to simplify their definition of a Path to a list of functions.
    if all([isinstance(a, FunctionType) for a in actions]):
        return [action.Action(functions=actions)]
    return actions


def normalize_path_enum(paths: dict, path_enum: EnumMeta = None):
    """If path_enum was not provided, generate one automatically."""
    if not path_enum:
        try:
            path_enum = utils.generate_enum(paths)
            paths = normalize_paths(path_enum, paths)
        except KeyError as e:
            raise lpipe.exceptions.InvalidConfigurationError from e
    return paths, path_enum
