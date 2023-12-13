"""
Classes that signifies parts of a forum.
"""
from .protocols.forum import *
from .exceptions import *
from dataclasses import dataclass, InitVar
from typing import TypeVar, Generic, Any

T = TypeVar("T")


class _IndexedAddons:
    """Addons for classes inheriting Indexed."""

    def update(self, method=str) -> None:
        """See :py:class:`Indexed`.
        
        :param method: The method to use.
        :raise IncompleteError: Some necessary fields are not defined.
        """
        attrs = dir(self)
        method_name = "update_" + method
        if method_name in attrs:
            getattr(self, method_name)(self)
        else:
            raise NotImplementedError(f"method {method} not implemented")

    def submit(self, method=str) -> None:
        """See :py:class:`Indexed`.
        
        :param method: The method to use.
        :raise IncompleteError: Some necessary fields are not defined."""
        attrs = dir(self)
        method_name = "submit_" + method
        if method_name in attrs:
            getattr(self, method_name)(self)
        else:
            raise NotImplementedError(f"method {method} not implemented")


@dataclass
class Page(Generic[T]):
    """A class representing a page.
    
    This object is polymorphic; it can support pages of different content types.

    :ivar hierarchy: The forum ID.
    :ivar current_page: The current page number.
    :ivar total_pages: The total pages.
    :ivar contents: The contents of the page."""
    hierarchy: list[tuple[str, str]]
    current_page: int
    total_pages: int
    contents: list[TypedDict]
    content_type: InitVar[T]

    def __post_init__(self, content_type: T):
        # cast self.contents with content_type
        self.contents = [content_type(**x) for x in self.contents]


@dataclass
class User(Indexed, _IndexedAddons):
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


class Topic(Indexed, _IndexedAddons):
    """A type that contains information about a topic. 

    :ivar tid: The topic ID.
    :ivar topic_name: The topic name.
    :ivar pages: The amount of pages the topic has
    """
    tid: int = None
    topic_name: str = None
    pages: int = None



@dataclass
class Message(Topic, _IndexedAddons):
    """Class that represents a message.

    A message (usually called a post) is the smallest unit of a forum. It carries
    a string of text as the content of the message, consisting of text, images,
    links, etc. It also carries other metadata like date of post and the user that 
    posted this post.
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

    def submit_post(self):
        """POST this message on the specified :py:ivar:`tid`."""
        if self.tid is None:
            raise IncompleteError("tid not specified")
        

