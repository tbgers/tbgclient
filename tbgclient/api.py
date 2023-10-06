"""
Contains functions to communicate with the TBG server.
"""

import requests
from .exceptions import RequestError

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


def get_topic_page(session: requests.Session, tid: int, mid: int | str = 0) \
    -> requests.Response:
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
    return request(session, "GET", FORUM_URL + f"?topic={tid}.{mid}")