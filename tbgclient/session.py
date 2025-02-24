"""
A module that contains classes for sessions.
"""
from multiprocessing.process import BaseProcess
import requests
from requests.cookies import RequestsCookieJar
from . import api
from asyncio import current_task, Task
from threading import current_thread, Thread
from multiprocessing import current_process
from typing import Optional, Union, Any, Self, TypeVar, Generic, TYPE_CHECKING
if TYPE_CHECKING:
    import tbgclient

"""
Since allowing different tasks, threads, or process clobbering the same stack
would be disastrous, we distinguish them so that each of them have their own
session stack.
"""

_sessions = {}
default_session: Optional["Session"] = None
T = TypeVar("T")


def get_context() -> tuple[Union[Task, ..., None], Thread, "BaseProcess"]:
    """Get the current context.
    :rtype: (Task | ... | None, Thread, Process)
    """
    task: Union[Task, ..., None]
    try:
        task = current_task()
    except RuntimeError:
        task = ...  # to distinguish it with None
    thread = current_thread()
    process = current_process()
    return task, thread, process


def push_session(session: "Session") -> None:
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

    def __init__(self: Self, get_sess_id: bool = False) -> None:
        self.session = requests.Session()
        self.cookies = RequestsCookieJar()
        if get_sess_id:
            # Get the PHPSESSID token.
            self.request("GET", api.FORUM_URL, allow_redirects=False)
        pass

    def login(self: Self, username: str, password: str) -> None:
        """Logs in the session to a user.
        :param username: The username.
        :param password: The password.
        """
        res = api.login(self, username, password)
        self.cookies.update(res.cookies)

    def request(self: Self, *args: Any, **kwargs: Any) -> requests.Response:
        """Do a request using this Session's cookie jar."""
        if "cookies" in kwargs:
            kwargs["cookies"] = {**kwargs["cookies"], **self.cookies}
        res = self.session.request(*args, **kwargs)
        self.cookies.update(res.cookies)
        return res

    def __enter__(self: Self) -> Self:
        """Use this session for the following context."""
        push_session(self)
        return self

    def __exit__(self: Self, exc_type: Exception, exc_value: Any,
                 traceback: Any) -> None:
        # check if someone has tampered with the stack
        popped = pop_session()
        if popped is not self:
            raise RuntimeError("Stack mismatch, did something tampered it?")

    def make_default(self: Self) -> None:
        """Make this Session object the default for requests."""
        global default_session
        default_session = self

    def get_message(self: Self, mid: int, method: str = "get"
                    ) -> "SessionContext[tbgclient.forum.Message]":
        """Gets a message with the specified message ID.

        The result is wrapped in a :py:class:`SessionContext`.
        :param mid: The message ID.
        :param method: The method to use. See
                       :py:class:`tbgclient.forum.Message`.
        """
        from .forum import Message
        return Message(mid=mid).using(self).update(method=method)

    def get_topic(self: Self, tid: int, method: str = "get"
                  ) -> "SessionContext[tbgclient.forum.Topic]":
        """Gets a topic with the specified topic ID.

        The result is wrapped in a :py:class:`SessionContext`.
        :param tid: The topic ID.
        :param method: The method to use. See
                       :py:class:`tbgclient.forum.Topic`.
        """
        from .forum import Topic
        return Topic(tid=tid).using(self).update(method=method)


class UsesSession:
    """A mixin for those that uses a session.

    This provides the property :py:ivar:`session` which is the session used in
    this context, along other things pertaining to session usage.
    """
    @property
    def session(self: Self) -> Session:
        context = get_context()
        if context not in _sessions:
            if default_session is None:
                raise RuntimeError("No default session is defined")
            return default_session
        return _sessions[context][-1]

    def using(self: Self, session: Session) -> "SessionContext":
        """Wrap this object in a new :py:class:`SessionContext`."""
        return SessionContext(session, self)


UsingSession = TypeVar("UsingSession", bound=UsesSession)


class SessionContext(Generic[UsingSession]):
    """A portable :py:class:`Session` context.

    This class wraps some object :py:ivar:`value` that inherits
    :py:class:`UsesSession` to use :py:ivar:`session`. The value wrapped
    will have their calls be under the session context of :py:ivar:`session`.

    :py:class:`SessionContext` also intercepts calls to :py:ivar:`value` to
    determine whether or not to keep the context. The context is kept if the
    value returned also inherits :py:class:`UsesSession`.
    """
    session: Session
    value: UsingSession

    def __init__(self: Self, session: Session, value: UsingSession) -> None:
        self.session = session
        if UsesSession not in type(value).__bases__:
            raise ValueError("Only values that uses sessions can be used")
        self.value = value

    def __getattr__(self: Self, name: str) -> Any:
        attr = getattr(self.value, name)
        # duck check if `attr` is callable
        try:
            attr.__call__
            # if `attr` is callable, wrap it onto a wrapper which decides
            # whether to keep the context or not

            def wrapper(*args: Any, **kwargs) -> Any:
                with self.session:
                    result = attr(*args, **kwargs)
                if UsesSession in type(result).__bases__:
                    # if the result uses a session, update this session
                    # to use this value
                    self.value = result
                    return self
                else:
                    # if not, just return the result as it is,
                    # thereby losing the context in the process
                    return result
            return wrapper
        except AttributeError:
            # if `attr` is not callable, return it as it is
            return attr

    def using(self: Self, session: Session) -> "SessionContext":
        """Create a new :py:class:`SessionContext` using the specified
        session."""
        return SessionContext(session, self.value)
