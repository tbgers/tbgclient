"""
Provides a way to get, post, and modify posts on the TBGs.
"""

from . import api
from . import exceptions

from .forum import Message, Topic, User, Page, Search, Alert
from .session import Session
from .protocols.forum import Smilies, PostIcons, UserGroup

Session().make_default()


# These convenience functions provide similar actions to frameworks like
# scratchattach


def get_message(mid: int, method: str = "get") -> Message:
    """Gets a message with the specified message ID.

    :param mid: The message ID.
    :param method: The method to use. See
                   :py:class:`tbgclient.forum.Message`.
    """
    return Message(mid=mid).update(method=method)


def get_topic(tid: int, method: str = "get") -> Topic:
    """Gets a topic with the specified topic ID.

    :param tid: The topic ID.
    :param method: The method to use. See
                   :py:class:`tbgclient.forum.Topic`.
    """
    from .forum import Topic
    return Topic(tid=tid).update(method=method)


def post_message(tid: int, subject: str, content: str, method: str = "post",
                 **kwargs) -> Message:
    """Post a message with the specified topic ID.
    For other keyword arguments, see :py:class:`tbgclient.forum.Message`.

    :param tid: The destination topic ID.
    :param subject: The subject of the message.
    :param content: The content of the message.
    :param method: The method to use. See
                   :py:class:`tbgclient.forum.Message`."""
    return (
        Message(tid, subject=subject, content=content, **kwargs)
        .submit(method=method)
    )


search = Search


__all__ = [
    "api", "exceptions", "Message", "Topic", "User", "Page", "Session",
    "Smilies", "PostIcons", "UserGroup", "Search", "Alert",
]
