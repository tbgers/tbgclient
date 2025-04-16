"""
Classes for use with the TBGs Chat.
"""

from collections import namedtuple
from .forum import User
from .parsers.chat import parse_response
from .protocols.forum import UserData
from datetime import datetime
from typing import Self, TYPE_CHECKING, Generator
from requests import Response
if TYPE_CHECKING:
    import tbgclient


class Message(namedtuple("_Message", [
    "mid", "user", "cid", "content", "date"
])):
    """A class representing a chat message.

    .. note:: This should not be confused with
    :py:class:`tbgclient.forum.Message`."""

    mid: int
    """The message ID."""
    user: User
    """The poster of this message."""
    cid: int
    """The channel ID of this message."""
    content: str
    """The message content."""
    date: str | datetime
    """The date this message is posted."""

    def __new__(cls: "Message", *,
                mid: int, user: UserData, cid: int,
                content: str, date: datetime) -> None:
        return super().__new__(cls, mid, User(**user), cid, content, date)

    @property
    def author(self: Self) -> None:
        """Alias of :py:attr:`user`."""
        return self.user


class ChatConnection:
    """A class that manages connections to the TBGs chat.

    Retrieving messages is done using the :py:func:`poll` function.
    Messages are then stored in a buffer that can be accessed with the
    :py:func:`messages` generator.

    Usage::
        >>> session = Session()
        >>> session.login("user", "pass")
        >>> chat = ChatConnection(session)
        >>> while True:
        ...     chat.poll()
        ...     for msg in chat.messages():
        ...         print(msg)
    """

    last_mid = None
    users: list[User]
    """List of online users in the channel."""
    cid: int
    """The current channel ID of this connection."""

    def __init__(self: Self, session: "tbgclient.Session") -> None:
        self.session = session
        self.__buffer = {}
        self.__read_mid = None
        self.cid = 0  # Public

    def poll(self: Self) -> dict[str, str]:
        """Poll the server to retrieve the recent messages.

        :return: The information of this connection.
        :rtype: dict[str, str]"""
        res = self.session.request(
            "GET", "https://tbgforums.com/forums/chat/",
            params={
                **({"lastID": self.last_mid}
                    if self.last_mid is not None
                    else {}),
                "ajax": "true",
                "channelID": str(self.cid),
            },
        )
        res = parse_response(res.content)

        # Put the messages in a buffer
        # At the same time, update __read_mid and __last_mid
        for msg in res["messages"]:
            if self.__read_mid is None:
                self.__read_mid = msg["mid"]
            if self.last_mid is None or self.last_mid < msg["mid"]:
                self.last_mid = msg["mid"]
            self.__buffer[msg["mid"]] = Message(**msg)
        self.users = [User(data) for data in res["users"]]
        self.cid = res["infos"].get("channelID", self.cid)

        return res["infos"]

    def messages(self: Self) -> Generator[Message, None, None]:
        """A generator that iterates through messages.

        .. note:: When the chat is polled for the first time, some past
        messages are put in the buffer, which may be undesired. To prevent
        this, you can empty the buffer by calling :py:func:`clear_buffer`:
        .. code-block:: python
            chat.poll()
            chat.clear_buffer()
            while True:
                ..."""
        while len(self.__buffer) > 0:
            if self.__read_mid in self.__buffer:
                yield self.__buffer[self.__read_mid]
                del self.__buffer[self.__read_mid]  # save memory
            self.__read_mid += 1
        # HACK: need to backtrack to prevent infinite loop
        self.__read_mid -= 1

    def clear_buffer(self: Self) -> None:
        """Clear the message buffer."""
        for _ in self.messages():
            pass

    def send(self: Self, message: str) -> Response:
        """Send a message to the server. This also accept commands."""
        res = self.session.request(
            "POST", "https://tbgforums.com/forums/chat/",
            data={"lastID": self.last_mid, "text": message},
            params={"ajax": "true"},
        )
        res = parse_response(res.content)
        self.cid = res["infos"].get("channelID", self.cid)

        return res
