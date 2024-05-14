"""
Contains functions to communicate with the TBG server.
"""

import requests
from .exceptions import RequestError
import urllib.parse
from . import parser
from .protocols.forum import PostIcons

FORUM_URL = "https://tbgforums.com/forums/index.php"


def request(session: requests.Session, method: str, url: str, 
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
    if res.status_code > 400:
        raise RequestError(f"{method} {url} returns {res.status_code}", response=res)
    return res


def do_action(session: requests.Session, action: str, method: str = "GET",  
              params: dict[str, str] = {}, queries: dict[str, str] = {}, 
              **kwargs) -> requests.Response:
    """Sends an action to the server.

    An action is a forum feature that is executed when the URL contains the 
    query parameter ``action``. This parameter may contain other parameters
    seperated by semicolons, with the action name written first.

    :param session: The session used.
    :type session: requests.Session
    :param method: The request method.
    :type method: str
    :param action: The action name.
    :type action: str
    :param params: The parameters of the action.
    :type params: dict[str, str]
    :param queries: Additional queries for the action.
    :type params: dict[str, str]
    :return: The response.
    :rtype: requests.Response
    """
    params_string = "".join(
        f";{preprocess(k)}={preprocess(v)}" 
        for k, v in params.items()
        for preprocess in (lambda x: urllib.parse.quote(x, safe=''),)
        # poorman's version of "where ... = ..."
    )
    return request(session, method, FORUM_URL,
                   params = {**queries, "action": action + params_string},
                   **kwargs)


def get_topic_page(session: requests.Session, tid: int, mid: int | str = 0, 
                   **kwargs) -> requests.Response:
    """GETs a page of a topic.

    :param session: The session used.
    :type session: requests.Session
    :param tid: The topic ID.
    :type tid: int
    :param mid: The message ID. This could also be ``"new"`` for the latest post.
    :type mid: int | str
    :return: The response.
    :rtype: requests.Response
    """
    return request(session, "GET", FORUM_URL + f"?topic={tid}.{mid}", **kwargs)


def post_message(session: requests.Session, tid: int, message: str, 
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
    :param icon: The message icon.
    :type icon: str | PostIcons
    :return: The response.
    :rtype: requests.Response
    """
    # first we get the nonce values (and other hidden inputs I guess)
    topic_res = do_action(session, "post2", queries={"topic": tid}, **kwargs)
    nonce = parser.get_hidden_inputs(topic_res.text)
    # print(nonce)

    # then we post the reply
    res = do_action(
        session,
        "post2",
        method = "POST",
        data = {
            "message": message,
            "subject": subject,
            "icon": icon.value if type(icon) is PostIcons else icon, 
            "post": "Post",
            "goback": "0",
            **nonce,
        },
        cookies = topic_res.cookies,
        allow_redirects = False,  # the redirect doesn't set any cookie
    )
    return res


def login(session: requests.Session, username: str, password: str, 
          **kwargs) -> requests.Response:
    """Logs in to the server.
    
    When given the correct credentials, the returned request will carry
    the session cookie for the user. Don't rely on ``session`` storing them
    as cookies stored on ``request.Session`` are global."""

    # get form first to get nonce
    form_res = do_action(session, "login")
    # print(form_res.cookies)
    nonce = parser.get_hidden_inputs(form_res.text)

    # then login
    res = do_action(
        session,
        "login2",
        method = "POST",
        data = {
            "user": username, 
            "passwrd": password,
            "cookielength": "3153600",  # essentially forever
            **nonce
        },
        cookies = form_res.cookies,
        allow_redirects = False,  # the redirect doesn't set any cookie
        **kwargs
    )
    return res

