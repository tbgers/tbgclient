"""
Contains functions to communicate with the TBG server.
"""

import requests
from .exceptions import RequestError
import urllib.parse
from .parsers import forum as forum_parser
from .protocols.forum import PostIcons
from typing import Any, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from . import session

FORUM_URL = "https://tbgforums.com/forums/index.php"
TOPIC_PER_PAGE = 25  # Let's hope this constant is managed by admins only...
raise_on_error_code = True
Session = Union[requests.Session, "session.Session"]


def request(session: Session, method: str, url: str,
            **kwargs) -> requests.Response:
    """Sends a request.

    :param session: The session used.
    :type session: requests.Session
    :param method: The request method.
    :type method: str
    :param url: The URL of the request.
    :type url: str
    :raises RequestError: The request returns an error code (>= 400)
    :return: The response.
    :rtype: requests.Response
    """
    res = session.request(method, url, **kwargs)
    if res.status_code > 400 and raise_on_error_code:
        raise RequestError(f"{method} {res.url} returns {res.status_code}",
                           response=res)
    return res


def do_action(session: Session, action: str, method: str = "GET",
              params: dict[str, str] = {}, queries: dict[str, Any] = {},
              no_percents: bool = False, **kwargs) -> requests.Response:
    """Sends an action to the server.

    An action is a forum feature that is executed when the URL contains the
    query parameter ``action``.

    :param session: The session used.
    :type session: requests.Session
    :param method: The request method.
    :type method: str
    :param action: The action name.
    :type action: str
    :param params: The parameters of the action.
    :type params: dict[str, str]
    :param queries: Additional queries for the action.
    :type queries: dict[str, str]
    :param no_percents: Whether to deter %-escapes. Useful for some actions.
    :type no_percents: bool
    :return: The response.
    :rtype: requests.Response
    """

    def preprocess(x: str) -> str:
        return urllib.parse.quote(x, safe='')

    params_string = "".join(
        f";{preprocess(k)}={preprocess(v)}"
        if v is not None
        else f";{preprocess(k)}"
        for k, v in params.items()
    )
    payload = {**queries, "action": action + params_string}
    if no_percents:
        payload = urllib.parse.urlencode(payload, safe=';=')
    return request(session, method, FORUM_URL,
                   params=payload,
                   **kwargs)


def get_topic_page(session: Session, tid: int, idx: int | str = 0,
                   **kwargs) -> requests.Response:
    """GETs a page of a topic.

    :param session: The session used.
    :type session: requests.Session
    :param tid: The topic ID.
    :type tid: int
    :param idx: The message number. This could also be ``"new"`` for the \
        latest post.
    :type idx: int | str
    :return: The response.
    :rtype: requests.Response
    """
    return request(session, "GET", FORUM_URL + f"?topic={tid}.{idx}", **kwargs)


def get_message_page(session: Session, mid: int,
                     **kwargs) -> requests.Response:
    """GETs a page of a topic of the specified message ID.

    :param session: The session used.
    :type session: requests.Session
    :param mid: The message ID.
    :type mid: int
    :return: The response.
    :rtype: requests.Response
    """
    if "cookies" in kwargs and "PHPSESSID" not in kwargs["cookies"] \
       or "PHPSESSID" not in session.cookies:
        # Get the PHPSESSID token.
        res = session.request("GET", FORUM_URL, allow_redirects=False)
        kwargs["cookies"] = {
            **(kwargs["cookies"] if "cookies" in kwargs else {}),
            **res.cookies
        }
    return request(session, "GET", FORUM_URL + f"?msg={mid}", **kwargs)


def post_message(session: Session, tid: int, message: str,
                 subject: str = "Reply",
                 icon: str | PostIcons = PostIcons.STANDARD,
                 **kwargs) -> requests.Response:
    """Post a reply to the specified topic ID.

    :param session: The session used.
    :type session: requests.Session
    :param tid: The topic ID.
    :type tid: int
    :param message: The message content.
    :type message: str
    :param subject: The message subject.
    :type subject: str
    :param icon: The message icon.
    :type icon: str | PostIcons
    :return: The response.
    :rtype: requests.Response
    """
    # first we get the nonce values (and other hidden inputs I guess)
    topic_res = do_action(session, "post2", queries={"topic": tid}, **kwargs)
    nonce = forum_parser.get_hidden_inputs(topic_res.text)
    # print(nonce)

    # then we post the reply
    res = do_action(
        session,
        "post2",
        method="POST",
        data={
            "message": message,
            "subject": subject,
            "icon": icon.value if type(icon) is PostIcons else icon,
            "post": "Post",
            "goback": "0",
            **nonce,
        },
        cookies=topic_res.cookies,
        allow_redirects=False,  # the redirect doesn't set any cookie
    )
    return res


def edit_message(session: Session, mid: int, tid: int,
                 message: str, subject: str = "Reply",
                 icon: str | PostIcons = PostIcons.STANDARD,
                 reason: str = "",
                 **kwargs) -> requests.Response:
    """Edits a reply to the specified message ID on a topic ID.
    (Yes, the topic ID is required!)

    :param session: The session used.
    :type session: requests.Session
    :param mid: The message ID.
    :type mid: int
    :param tid: The topic ID.
    :type tid: int
    :param message: The message content.
    :type message: str
    :param subject: The message subject.
    :type subject: str
    :param icon: The message icon.
    :type icon: str | PostIcons
    :param reason: The reason for the edit.
    :type reason: str
    :return: The response.
    :rtype: requests.Response
    """
    # first we get the nonce values (and other hidden inputs I guess)
    topic_res = do_action(session, "post", queries={"msg": mid, "topic": tid},
                          **kwargs)
    nonce = forum_parser.get_hidden_inputs(topic_res.text)
    # print(nonce)

    # then we post the reply
    res = do_action(
        session,
        "post",
        method="POST",
        queries={"msg": mid},
        data={
            "topic": tid,
            "message": message,
            "subject": subject,
            "icon": icon.value if type(icon) is PostIcons else icon,
            "post": "Save",
            "goback": "0",
            "modify_reason": reason,
            **nonce,
        },
        cookies=topic_res.cookies,
        allow_redirects=False,  # the redirect doesn't set any cookie
    )
    return res


def login(session: Session, username: str, password: str,
          **kwargs) -> requests.Response:
    """Logs in to the server.

    When given the correct credentials, the returned request will carry
    the session cookie for the user.

    .. warning:: Don't rely on ``session`` storing them, as cookies stored
    on ``requests.Session`` are global."""

    # get form first to get nonce
    form_res = do_action(session, "login")
    # print(form_res.cookies)
    nonce = forum_parser.get_hidden_inputs(form_res.text)

    # then login
    res = do_action(
        session,
        "login2",
        method="POST",
        data={
            "user": username,
            "passwrd": password,
            "cookielength": "3153600",  # essentially forever
            **nonce
        },
        cookies=form_res.cookies,
        allow_redirects=False,  # the redirect doesn't set any cookie
        **kwargs
    )
    return res
