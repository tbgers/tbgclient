"""
Contains data classes that ``tbgclient`` uses.

These classes serve as session-less counterparts of the classes which inherit
them.
"""

from . import forum, chat

__all__ = ["forum", "chat"]
