from enum import Enum, EnumMeta
from typing import Union

from lpipe import exceptions, normalize, queue, utils


class Payload:
    def __init__(
        self,
        kwargs: dict,
        path: Union[Enum, str] = None,
        queue: queue.Queue = None,
        event_source=None,
    ):
        try:
            assert bool(path) != bool(queue)
        except AssertionError as e:
            raise exceptions.InvalidPayloadError() from e
        self.path = path
        self.queue = queue
        self.kwargs = kwargs
        self.event_source = event_source

    def validate(self, path_enum: EnumMeta = None):
        if self.path and path_enum:
            assert isinstance(normalize.normalize_path(path_enum, self.path), path_enum)
        elif self.queue:
            assert isinstance(self.queue, queue.Queue)
        return self

    def to_dict(self) -> dict:
        return {"path": self.path, "kwargs": self.kwargs}

    def _json(self):
        return self.to_dict()

    def __repr__(self):
        return utils.repr(self, ["path", "kwargs"])
