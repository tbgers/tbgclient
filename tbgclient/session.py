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
from typing import Optional, Union, Any, TypeVar, Generic, TYPE_CHECKING
try:
    # PORT: 3.10 and below doesn't have typing.Self
    from typing import Self
except ImportError:
    from typing_extensions import Self
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


class MISSING:
    """An internal sentinel value for non-asynchronous contexts,
    of which :py:func:`asyncio.current_task()` will raise an error for the lack
    of a running event loop."""


def get_context() -> tuple[Union[Task, MISSING, None], Thread, "BaseProcess"]:
    """Get the current context.
    :rtype: (Task | ... | None, Thread, Process)
    """
    task: Union[Task, MISSING, None]
    try:
        task = current_task()
    except RuntimeError:
        task = MISSING()
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
    user: "tbgclient.forum.User"

    def __init__(self: Self, get_sess_id: bool = False) -> None:
        self.session = requests.Session()
        self.cookies = RequestsCookieJar()
        self.user = None
        if get_sess_id:
            # Get the PHPSESSID token.
            self.request("GET", api.FORUM_URL, allow_redirects=False)
        pass

    def login(self: Self, username: str, password: str) -> None:
        """Logs in the session to a user.
        :param username: The username.
        :param password: The password.
        """
        import re
        from urllib.parse import urlparse
        from .forum import User
        res = api.login(self, username, password)
        self.cookies.update(res.cookies)
        # Get the user's ID.
        # Conveinently, SMF already included it on the query string =)
        url = urlparse(res.headers["location"])
        uid = re.search(r'member=(\d+)', url.query)
        self.user = User(name=username, uid=int(uid[1]))

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
        """Make this :py:class:`Session` object the default for requests."""
        global default_session
        default_session = self

    def __repr__(self: Self) -> str:
        return (
            # HACK: Need to avoid recursion loops!
            "<Session of User"
            f"(name={self.user.name!r}, uid={self.user.uid!r})>"
            if self.user is not None
            else "<Session of Guest>"
        )


class UsesSession:
    """A mixin for those that uses a session.

    This provides the property :py:attr:`session` which is the session used in
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

    This class wraps some object :py:attr:`value` that inherits
    :py:class:`UsesSession` to use :py:attr:`session`. The value wrapped
    will have their calls be under the session context of :py:attr:`session`.

    :py:class:`SessionContext` also intercepts calls to :py:attr:`value` to
    determine whether or not to keep the context. The context is kept if the
    value returned also inherits :py:class:`UsesSession`.
    """
    session: Session
    value: UsingSession

    def __init__(self: Self, session: Session, value: UsingSession) -> None:
        # We assigned __setattr__, so we have to use object's
        object.__setattr__(self, "session", session)
        if UsesSession not in type(value).__bases__:
            raise ValueError("Only values that uses sessions can be used")
        object.__setattr__(self, "value", value)

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

    def __setattr__(self: Self, name: str, value: Any) -> Any:
        return self.value.__setattr__(name, value)

    def using(self: Self, session: Session) -> "SessionContext":
        """Create a new :py:class:`SessionContext` using the specified
        session."""
        return SessionContext(session, self.value)

    def __repr__(self: Self) -> str:
        return f"<SessionContext of {self.session} for {self.value}>"

    # NOTE: Some functionality of Python (like for loops) requires these
    # functions to be explicitly written. (perhaps from attribute tests)
    def __iter__(self: Self) -> Any:
        return self.__getattr__("__iter__")()
