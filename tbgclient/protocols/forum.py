"""
Protocols that signifies parts of a forum.
"""

from typing import Protocol, TypeVar, TypedDict
from enum import Enum

T = TypeVar('T')


class Indexed(Protocol):
    """Protocol for anything that has an index (for example, messages)."""

    def update(self, method: str) -> None:
        """Updates this object.

        This function is to modify objects that already exists on the TBG server.
        
        :param method: The method to use.
        :raise IncompleteError: Some necessary fields are not defined.
        """
        raise NotImplementedError

    def submit(self, method: str) -> None:
        """Submit this object.
        
        This function is to create objects that don't exist on the TBG server.
        
        :param method: The method to use.
        :raise IncompleteError: Some necessary fields are not defined."""
        raise NotImplementedError
    

class PageData(TypedDict, total=False):
    """A type that contains information about a page.

    :ivar hiearchy: The forum ID.
    :ivar current_page: The current page number.
    :ivar total_pages: The total pages.
    :ivar contents: The contents of the page.
    """
    hierarchy: list[tuple[str, str]]
    current_page: int
    total_pages: int
    contents: list[dict]


class ForumData(TypedDict, total=False):
    """A type that contains information about a forum.

    :ivar fid: The forum ID.
    :ivar forum_name: The forum name.
    """
    fid: int
    forum_name: str


class TopicData(ForumData, total=False):
    """A type that contains information about a topic. 

    :ivar tid: The topic ID.
    :ivar topic_name: The topic name.
    :ivar pages: The amount of pages the topic has
    """
    tid: int
    topic_name: str
    pages: int


class UserGroup(Enum):
    """An enum of user groups used in the TBGs."""
    TBG = "TBGer"
    TBG_TEAM = "TBG Team"
    TBG_ADMIN = "TBG Administrator"
    TBG_WIKI = "TBG Wiki Bureaucrats"
    TBG_WIKI_ADMIN = "TBG Wiki Administrators"
    TBG_MOD = "TBG Moderators"
    RETIRED_TBG_MOD = "Retired TBG Moderators"


class UserData(TypedDict, total=False):
    """A type that contains information about a user. 

    :ivar uid: The user ID.
    :ivar name: The user name.
    :ivar avatar: The avatar/profile picture of the user.
    :ivar group: The user group.
    :ivar posts: The total amount of posts this user has made.
    :ivar signature: The signature of this user.
    :ivar email: The email address of this user.
    :ivar edited: The date when this message was last edited.
    :ivar blurb: The personal text of this user.
    :ivar real_name: The real name of this user.
    :ivar location: The location of this user.
    :ivar social: The social names of this user.
    :ivar website: The website URL of this user. 
    :ivar gender: The gender of this user.
    """
    uid: int
    name: str
    avatar: str
    group: str | UserGroup
    posts: int
    signature: str
    email: str
    blurb: str
    location: str
    real_name: str
    social: dict[str, str]
    website: str
    gender: str


class MessageData(TopicData, total=False):
    """A type that contains information about a message. 

    :ivar mid: The message ID.
    :ivar title: The message title.
    :ivar date: The date when this message was posted.
    :ivar edited: The date when this message was last edited.
    :ivar content: The message content.
    :ivar user: The poster of the message.
    """
    mid: int
    subject: str  # yes, this exists in SMF.
    date: str
    edited: str | None
    content: str
    user: UserData
