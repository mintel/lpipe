from enum import Enum

from lpipe import queue, utils


class QueueType(Enum):
    RAW = 1  # This may be a Cloudwatch or manually triggered event
    KINESIS = 2
    SQS = 3


class Queue:
    """Represents a queue path in an Action.

    Note:
        Kinesis uses name.
        SQS uses name or url.

    Args:
        type (QueueType)
        path (str): Value of the "path" field set on the message we'll send to this queue.
        name (str, optional): Queue name
        url (str, optional): Queue URL/URI

    Attributes:
        type (QueueType)
        path (str)
        name (str)
        url (str)

    """

    def __init__(
        self, type: queue.QueueType, path: str = None, name: str = None, url: str = None
    ):
        assert name or url
        assert isinstance(type, queue.QueueType)
        self.type = type
        self.path = path
        self.name = name
        self.url = url

    def __repr__(self):
        return utils.repr(self, ["type", "name", "url"])
