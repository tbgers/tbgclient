"""
Data classes that signifies parts of the TBGs chat.

.. note::

    Some of these classes look and are named similar to the classes at
    :py:mod:`~tbgclient.data.forum`. However, they are not related to each
    other (aside from the data classes which inherits
    :py:mod:`tbgclient.data.utils.Data`) and are not interchangeable with one
    another.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
try:
    # PORT: 3.10 and below doesn't have typing.Self
    from typing import Self
except ImportError:
    from typing_extensions import Self
import re

from .utils import Data


class UserRole(Enum):
    """An enum of user roles used in the TBGs chat."""
    # names taken from ajaxChat.getRoleClass
    GUEST = "0"
    USER = "1"
    MODERATOR = "2"
    ADMIN = "3"
    CHAT_BOT = "4"
    CUSTOM_USER = "5"
    DEFAULT = None

    @classmethod
    def _missing_(cls: "UserRole", value: Any) -> "UserRole":
        return cls.DEFAULT

    def class_name(self: Self) -> str:
        """Return class names as returned by ``ajaxChat.getRoleClass``."""
        return re.sub("_(.)", lambda match: match[1].upper, self.name.lower)


@dataclass(kw_only=True)
class UserData(Data):
    """A type that contains information about a user."""

    uid: int
    """The user's ID."""
    name: str
    """The user's name."""
    role: UserRole
    """The user's role."""


@dataclass(kw_only=True)
class MessageData(Data):
    """A type that contains information about a message."""

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


@dataclass(kw_only=True)
class ResponseData(Data):
    """A type representing the response of the poll."""

    infos: dict[str, str]
    """Information about this session.
    This is only present when the user joins the channel."""
    users: list[UserData]
    """A list of online users."""
    messages: list[MessageData]
    """A list of the retrieved messages."""
