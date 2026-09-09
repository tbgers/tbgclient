"""
Provides a way to get, post, and modify posts on the TBGs.
"""

from . import api
from . import exceptions

from .forum import Message, Topic, User, Page, Search, Alert
from .session import Session
from .data.forum import Smilies, PostIcons, UserGroup

Session().make_default()


# These convenience functions provide similar actions to frameworks like
# scratchattach


def get_message(mid: int, method: str = "get") -> Message:
    """Gets a message with the specified message ID.

    :param mid: The message ID.
    :param method: The method to use. This should be "get" or "quotefast".
    """
    msg = Message(mid=mid)
    if method == "get":
        return msg.update_get()
    elif method == "quotefast":
        return msg.update_quotefast()
    else:
        raise ValueError("method should be either 'get' or 'quotefast'")


def get_topic(tid: int) -> Topic:
    """Gets a topic with the specified topic ID.

    :param tid: The topic ID.
    """
    from .forum import Topic
    return Topic(tid=tid).update()


def get_user(uid: int) -> User:
    """Gets a user with the specified user ID.

    :param uid: The user ID.
    """
    return User(uid=uid).update()


def post_message(tid: int, subject: str, content: str, **kwargs) -> Message:
    """Post a message with the specified topic ID.
    For other keyword arguments, see :py:class:`tbgclient.forum.Message`.

    :param tid: The destination topic ID.
    :param subject: The subject of the message.
    :param content: The content of the message.
    """
    return (
        Message(tid=tid, subject=subject, content=content, **kwargs)
        .submit_post()
    )


def edit_message(mid: int, tid: int, subject: str, content: str,
                 **kwargs) -> Message:
    """Edit a message with the specified topic ID and message ID.
    For other keyword arguments, see :py:class:`tbgclient.forum.Message`.

    :param tid: The destination topic ID.
    :param subject: The subject of the message.
    :param content: The content of the message.
    """
    return (
        Message(mid=mid, tid=tid, subject=subject, content=content, **kwargs)
        .submit_edit()
    )


def login(username: str, password: str) -> Session:
    """Make a logged-in session and return it.
    This will also make the session the default session.

    :return: The logged-in session.
    """
    session = Session()
    session.login(username, password)
    session.make_default()
    return session


search = Search

get_alerts = Alert.pages


__all__ = [
    "api", "exceptions", "Message", "Topic", "User", "Page", "Session",
    "Smilies", "PostIcons", "UserGroup", "Search", "Alert",
]
