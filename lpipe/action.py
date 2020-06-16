from enum import Enum
from types import FunctionType
from typing import List, Union

from lpipe import queue, utils


class Action:
    def __init__(
        self,
        functions: List[FunctionType] = [],
        paths: List[Union[str, Enum]] = [],
        queues: List[queue.Queue] = [],
        required_params=None,
        include_all_params=False,
    ):
        assert functions or paths or queues
        self.functions = functions
        self.paths = paths
        self.queues = queues
        self.required_params = required_params
        self.include_all_params = include_all_params

    def __repr__(self):
        return utils.repr(self, ["functions", "paths", "queues"])

    def copy(self):
        return type(self)(
            functions=self.functions,
            paths=[str(p).split(".")[-1] for p in self.paths],
            queues=self.queues,
            required_params=self.required_params,
        )
