from enum import Enum
from types import FunctionType
from typing import List, Union

from lpipe import queue, utils


class Action:
    def __init__(
        self,
        functions: List[FunctionType] = [],
        paths: List[Union[str, Enum]] = [],
        required_params=None,
        include_all_params=False,
    ):
        assert functions or paths
        self.functions = functions
        self.paths = paths
        self.required_params = required_params
        self.include_all_params = include_all_params

    def __repr__(self):
        return utils.repr(self, ["functions", "paths"])

    def copy(self):
        return type(self)(
            functions=self.functions,
            paths=[
                p if isinstance(p, queue.Queue) else str(p).split(".")[-1]
                for p in self.paths
            ],
            required_params=self.required_params,
        )
