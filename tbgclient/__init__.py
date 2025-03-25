"""
Provides a way to get, post, and modify posts on the TBGs.
"""

from . import api
from . import exceptions

from .forum import Message, Topic, User, Page, Search
from .session import Session
from .protocols.forum import Smilies, PostIcons, UserGroup

Session().make_default()


__all__ = [
    "api", "exceptions", "Message", "Topic", "User", "Page", "Session",
    "Smilies", "PostIcons", "UserGroup", "Search"
]
