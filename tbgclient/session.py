"""
A module that contains classes for sessions.
"""
from multiprocessing.process import BaseProcess
import requests
from requests.cookies import RequestsCookieJar
from .forum import *
from . import api
from asyncio import current_task, Task
from threading import current_thread, Thread
from multiprocessing import current_process
from typing import Optional, Union

"""
Since allowing different tasks, threads, or process clobbering the same stack 
would be disastrous, we distinguish them so that each of them have their own
session stack.
"""

_sessions = {}
default_session: Optional["Session"] = None


def get_context() -> tuple[Union[Task, "ellipsis", None], Thread, "BaseProcess"]:
    """Get the current context.
    :rtype: (Task | ... | None, Thread, Process)
    """
    task: Union[Task, "ellipsis", None]
    try:
        task = current_task()
    except RuntimeError:
        task = ...  # to distinguish it with None
    thread = current_thread()
    process = current_process()
    return task, thread, process


def push_session(session):
    """Push this session to the current session stack."""
    context = get_context()
    if context not in _sessions:
        _sessions[context] = []
    _sessions[context].append(session)


def pop_session() -> "Session":
    """Pop a session from the current session stack."""
    context = get_context()
    popped = _sessions[context].pop()
    if _sessions[context] == []:
        # if the stack is blank, we can assume this context is finished,
        # and we can delete it to save memory
        del _sessions[context]
    return popped


class Session:
    """A TBG session.
    """
    session: requests.Session
    cookies: RequestsCookieJar

    def __init__(self, get_sess_id=False):
        self.session = requests.Session()
        self.cookies = RequestsCookieJar()
        if get_sess_id:
            # Get the PHPSESSID token.
            self.request("GET", api.FORUM_URL, allow_redirects=False)
        pass

    def login(self, username, password):
        """Logs in the session to a user.
        :param username: The username.
        :param password: The password.
        """
        res = api.login(self, username, password, cookies=self.cookies)
        self.cookies.update(res.cookies)

    def request(self, *args, **kwargs):
        """Do a request using this Session's cookie jar."""
        if "cookies" in kwargs:
            kwargs["cookies"] = {**kwargs["cookies"], **self.cookies}
        res = self.session.request(*args, **kwargs)
        self.cookies.update(res.cookies)
        return res

    def __enter__(self):
        """Use this session for the following context."""
        push_session(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # check if someone has tampered with the stack
        popped = pop_session()
        if popped is not self:
            raise RuntimeError("Stack mismatch, did something tampered it?")
    
    def make_default(self):
        """Make this Session object the default for requests."""
        global default_session
        default_session = self


class UsesSession:
    """A mixin for those that uses a session.
    
    This provides the property :py:ivar:`session` which is the session used in this
    context."""
    @property
    def session(self):
        context = get_context()
        if context not in _sessions:
            if default_session is None:
                raise RuntimeError("No default session is defined")
            return default_session
        return _sessions[context][-1]

