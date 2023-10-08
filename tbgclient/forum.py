"""
Classes that signifies parts of a forum.
"""
from .protocols.forum import *
from dataclasses import dataclass, InitVar
from typing import TypeVar, Generic

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """A class representing a page.
    
    This object is polymorphic; it can support pages of different content types.

    ivar hiearchy: The forum ID.
    :ivar current_page: The current page number.
    :ivar total_pages: The total pages.
    :ivar contents: The contents of the page."""
    hierarchy: list[tuple[str, str]]
    current_page: int
    total_pages: int
    contents: list[TypedDict]
    content_type: InitVar[T]

    def __post_init__(self, content_type: type):
        # cast self.contents with content_type
        self.contents = [content_type(**x) for x in self.contents]


@dataclass
class User(Indexed):
    """Class that represents a user."""
    uid: int = None
    name: str = None
    avatar: str = None
    group: str | UserGroup = None
    posts: int = None
    signature: str = None
    email: str = None
    blurb: str = None
    location: str = None
    real_name: str = None
    social: dict[str, str] = None
    website: str = None
    gender: str = None


@dataclass
class Message(Indexed):
    """Class that represents a message.

    A message (usually called a post) is the smallest unit of a forum. It carries
    a string of text as the content of the message.
    """
    mid: int = None
    subject: str = None
    date: str = None
    edited: str | None = None
    content: str = None
    user: User | UserData = None

    def __post_init__(self):
        if type(self.user) is dict:
            self.user = User(**self.user)

