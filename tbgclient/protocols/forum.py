"""
Protocols that signifies parts of a forum.
"""

from typing import TypeVar, TypedDict, Generic
try:
    # PORT: 3.10 and below doesn't have typing.Self
    from typing import Self
except ImportError:
    from typing_extensions import Self
from enum import Enum
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

T = TypeVar('T')
try:
    # PORT: Until 3.11, you cannot create a class that
    # inherits TypedDict and Generic
    type("_inherit_test", (TypedDict, Generic[T]), {})
except TypeError:
    from typing_extensions import TypedDict


class Indexed(ABC):
    """ABC for anything that has an index (for example, messages)."""

    # RFE: it would be nicer if we can just match function under a prefix
    @abstractmethod
    def update(self: Self, method: str) -> Self:
        """Updates this object.

        This function is to modify objects that already exists on the TBG
        server.

        :param method: The method to use.
        :raise IncompleteError: Some necessary fields are not defined.
        """
        raise NotImplementedError

    @abstractmethod
    def submit(self: Self, method: str) -> Self:
        """Submit this object.

        This function is to create objects that don't exist on the TBG server.

        :param method: The method to use.
        :raise IncompleteError: Some necessary fields are not defined."""
        raise NotImplementedError


class Paged(ABC, Sequence, Generic[T]):
    """ABC for anything that has pages on it. (for example, topics)"""
    @abstractmethod
    def get_page(self: Self, page: int = 1) -> list[T]:
        """Get the specified page.

        Note that this function is 1-indexed; use the usual subscript
        expression for the 0-indexed version of this function."""
        raise NotImplementedError

    @abstractmethod
    def get_size(self: Self) -> int | None:
        """Return the length of this object. If the length is currently
        unknown, return `None`.

        For the best perfomance, this function should be cached."""
        raise NotImplementedError

    def __getitem__(self: Self, x: int) -> list[T]:
        x = round(x)
        length = self.__len__()
        if length is not None:  # currently unknown
            if x < 0:  # negative indicies wraps around
                x = length - x
            if x < 0 or x >= length:
                raise IndexError("list index out of range")
        return self.get_page(x + 1)

    def __len__(self: Self) -> int:
        return self.get_size()


class PageData(TypedDict, Generic[T], total=False):
    """A type that contains information about a page.
    """

    hierarchy: list[tuple[str, str]]
    """The hierarchy of this page."""
    current_page: int
    """The current page number."""
    total_pages: int
    """The total pages."""
    contents: list[T]
    """The contents of the page."""


class BoardData(TypedDict, total=False):
    """A type that contains information about a board.
    """

    bid: int
    """The board ID."""
    board_name: str
    """The board name."""


class TopicData(BoardData, total=False):
    """A type that contains information about a topic.

    :ivar tid: The topic ID.
    :ivar topic_name: The topic name.
    :ivar pages: The amount of pages the topic has
    """
    tid: int
    """The topic ID."""
    topic_name: str
    """The topic name."""


class UserGroup(Enum):
    """An enum of user groups used in the TBGs."""
    BANNED = "Banned"
    TBG = "TBGer"
    TBG_TEAM = "TBG Team"
    # TBG_ADMIN = "TBG Administrator"  # this is not a thing anymore
    TBG_WIKI = "TBG Wiki Bureaucrats"
    TBG_WIKI_ADMIN = "TBG Wiki Administrators"
    TBG_MOD = "TBG Moderators"
    RETIRED_TBG_MOD = "Retired TBG Moderators"


class PostIcons(Enum):
    """An enum of the post icons used in the TBGs."""
    # Yes, this is a thing now.
    STANDARD = "xx"
    THUMB_UP = "thumbup"
    THUMB_DOWN = "thumbdown"
    EXCLAMATION = "exclamation"
    QUESTION = "question"
    LAMP = "lamp"
    SMILE = "smiley"
    ANGRY = "angry"
    CHEESY = "cheesy"
    GRIN = "grin"
    SAD = "sad"
    WINK = "wink"
    POLL = "poll"


class Smilies(Enum):
    """An enum of the smilies icons used in the TBGs."""
    # Note: Uses file names for the member names.
    SMILE = ":)"
    NEUTRAL = ":|"
    SAD = ":("
    YIKES = ":o"
    BIG_SMILE = ":D"
    LOL = ":lol:"
    HMM = ":/"
    MAD = "D:<"
    WINK = ";)"
    TONGUE = ":P"
    ROLL = ":roll:"
    COOL = "B)"


class SearchType(Enum):
    """Corresponds to the Match input (searchtype) on the Search form."""
    ALL_WORDS = "1"
    """Match all words."""
    ANY_WORDS = "2"
    """Match any words."""


class SortBy(Enum):
    """Corresponds to the Sort by input (sort) criteria on the Search form."""
    RELEVANCE = "relevance"
    """Sort by relevance; how many word matches."""
    REPLIES = "num_replies"
    """Sort by number of replies of the topic the message is posted."""
    MESSAGE_ID = "id_msg"
    """Sort by the message ID; generally this corresponds to their age."""


class SortOrder(Enum):
    """Corresponds to the Sort by input (sort) ordering on the Search form."""
    ASC = "asc"
    """Sort ascending."""
    DESC = "desc"
    """Sort descending."""


class UserData(TypedDict, total=False):
    """A type that contains information about a user.
    """

    uid: int
    """The user's ID."""
    name: str
    """The user's name."""
    avatar: str
    """The avatar/profile picture of the user."""
    group: str | UserGroup
    """The user's group."""
    posts: int
    """The total amount of posts this user has made."""
    signature: str
    """The signature of this user."""
    email: str
    """The email address of this user."""
    blurb: str
    """The personal text of this user."""
    location: str
    """The location of this user."""
    real_name: str
    """The real name of this user."""
    social: dict[str, str]
    """Other identities of this user across different social medias."""
    website: str
    """The website URL of this user."""
    gender: str
    """The gender of this user."""


class MessageData(TopicData, total=False):
    """A type that contains information about a message.
    """

    mid: int
    """The message ID."""
    subject: str  # yes, this exists in SMF.
    """The message subject."""
    date: str | datetime
    """The date when this message was posted."""
    edited: str | None
    """The date when this message was last edited."""
    content: str
    """The message content."""
    user: UserData
    """The poster of the message."""
    icon: str | PostIcons
    """The icon used in the message. Usually this is invisible."""
