"""
Protocols that signifies parts of the TBGs chat.
"""

from typing import TypedDict
from .forum import UserData
from datetime import datetime


class MessageData(TypedDict):
    """A type that contains information about a message.

    .. note:: This should not be confused with
    :py:class:`tbgclient.protocols.forum.MessageData`."""

    mid: int
    """The message ID."""
    user: UserData
    """The poster of this message."""
    cid: int
    """The channel ID of this message."""
    content: str
    """The message content."""
    date: str | datetime
    """The date this message is posted."""


class ResponseData(TypedDict):
    """A type representing the response of the poll."""

    infos: dict[str, str]
    """Information about this session.
    This is only present when the user joins the channel."""
    users: list[UserData]
    """A list of online users."""
    messages: list[MessageData]
    """A list of the retrieved messages."""
