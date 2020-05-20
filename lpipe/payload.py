from enum import Enum, EnumMeta
from typing import Union

from lpipe import normalize, queue, utils


class Payload:
    def __init__(self, path: Union[Enum, str], kwargs: dict, event_source=None):
        self.path = path
        self.kwargs = kwargs
        self.event_source = event_source

    def validate(self, path_enum: EnumMeta = None):
        if path_enum:
            assert isinstance(
                normalize.normalize_path(path_enum, self.path), path_enum
            ) or isinstance(self.path, queue.Queue)
        else:
            assert isinstance(self.path, queue.Queue)
        return self

    def to_dict(self) -> dict:
        return {"path": self.path, "kwargs": self.kwargs}

    def __repr__(self):
        return utils.repr(self, ["path", "kwargs"])
