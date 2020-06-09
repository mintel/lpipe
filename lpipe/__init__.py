"""
lpipe
~~~~~~~~~

Lambda Pipeline, a framework for writing clear, minimal Python FAAS
"""

# flake8: noqa

from lpipe._version import __version__
from lpipe.action import Action
from lpipe.payload import Payload
from lpipe.pipeline import process_event
from lpipe.queue import Queue, QueueType
