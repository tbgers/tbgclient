"""
Classes that signifies parts of a forum.
"""
from .session import UsesSession
from .protocols.forum import (
    Indexed, UserGroup, Paged, PostIcons, UserData, SearchType, SortBy,
    SortOrder
)
# from .protocols.forum import
from .exceptions import RequestError, IncompleteError
from . import api
from .parsers import forum as forum_parser
from dataclasses import dataclass, InitVar, fields, field
from typing import TypeVar, Generic, ClassVar
try:
    # PORT: 3.10 and below doesn't have typing.Self
    from typing import Self
except ImportError:
    from typing_extensions import Self
from warnings import warn
from collections.abc import Iterator
import zlib
import base64
from datetime import datetime, date

T = TypeVar("T")


def check_fields(self: Self, *fields) -> Self:
    """Checks the field for this instance."""
    missing = []
    for field in fields:  # noqa: F402
        if getattr(self, field) is None:
            missing.append(field)
    if missing != []:
        raise IncompleteError(missing)


class _Indexed(Indexed):
    """An altered version of Indexed."""

    default_update_method = "get"
    default_submit_method = "post"

    def update(self: Self, method: str = None, **kwargs) -> Self:
        """See :py:class:`Indexed`.

        :param method: The method to use.
        :raise IncompleteError: Some necessary fields are not defined.
        """
        if method is None:
            method = self.default_update_method
        attrs = dir(self)
        my_fields = {field.name for field in fields(self)}
        method_name = "update_" + method

        excess_kwargs = {}
        for k, v in kwargs.items():
            if k in my_fields:
                setattr(self, k, v)
            else:
                excess_kwargs[k] = v

        if method_name in attrs:
            return getattr(self, method_name)(**excess_kwargs)
        else:
            raise NotImplementedError(f"method {method} not implemented")

    def submit(self: Self, method: str = None, **kwargs) -> Self:
        """See :py:class:`Indexed`.

        :param method: The method to use.
        :raise IncompleteError: Some necessary fields are not defined."""
        if method is None:
            method = self.default_submit_method
        attrs = dir(self)
        my_fields = {field.name for field in fields(self)}
        method_name = "submit_" + method

        excess_kwargs = {}
        for k, v in kwargs.items():
            if k in my_fields:
                setattr(self, k, v)
            else:
                excess_kwargs[k] = v

        if method_name in attrs:
            return getattr(self, method_name)(**excess_kwargs)
        else:
            raise NotImplementedError(f"method {method} not implemented")


@dataclass
class Page(Generic[T]):
    """A class representing a page.

    This object is polymorphic; it can support pages of different content
    types.
    """

    hierarchy: list[tuple[str, str]]
    """The hierarchy of this page."""
    current_page: int
    """The current page number."""
    total_pages: int
    """The total pages."""
    contents: list[T]
    """The contents of the page."""
    content_type: InitVar[T]

    def __post_init__(self: Self, content_type: T) -> None:
        # cast self.contents with content_type
        self.contents = [
            content_type(**x) for x in self.contents
        ]

    def __iter__(self: Self) -> Iterator[T]:
        return iter(self.contents)


@dataclass
class User(UsesSession, _Indexed):
    """A class that represents a user."""
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

    default_submit_method: ClassVar[str] = "profile"

    def update_get(self: Self) -> Self:
        """GET this user on the specified :py:ivar:`uid`."""
        check_fields(self, "uid")
        res = api.do_action(
            self.session,
            "profile",
            params={"u": str(self.uid)},
            no_percents=True
        )
        forum_parser.check_errors(res.text, res)
        parsed = forum_parser.parse_profile(res.text)
        # The parsed dictionary doesn't include the uid
        parsed["uid"] = self.uid
        self.__init__(**parsed)
        return self

    def submit_profile(self: Self,
                       birthday: datetime | date | None = None) -> Self:
        """Update this user's profile.

        .. warning::

            Keep in mind that the :py:attr:`signature` attribute is expecting
            a BBC value, not the HTML string that :py:func:`update_get`
            returns. If you just updated this object using that function, this
            *will* be escaped by SMF, which may be undesirable.

            To avoid this, make sure you update the signature, or just blank
            it out.

            .. code-block:: python

                user.update()
                user.signature = "something"
                user.submit()

        :param birthday: The birthday of this user. If `None`, leave it
                         unchanged.
        """
        check_fields(self, "uid")
        gender_idx = {
            "none": 0,
            "male": 1,
            "female": 2,
            "non-binary": 3,
        }
        social_idx = {
            "jabber": "cust_jabber",
            "msn messenger": "cust_msn",
            "aol im": "cust_aolim",
            "yahoo! messenger": "cust_yahoo"
        }
        res = api.edit_profile(
            self.session,
            self.uid,
            self.avatar,
            self.blurb,
            None,
            self.signature,
            # We didn't store the website title
            self.website,
            self.website,
            {
                "cust_real": self.real_name,
                "cust_loca": self.location,
                **{
                    social: ""
                    for social in social_idx.values()
                },
                **{
                    social_idx[k.lower()]: v
                    for k, v in self.social.items()
                    if k.lower in social_idx
                },
                "cust_gender": gender_idx[str(self.gender).lower()]
            },
        )
        forum_parser.check_errors(res.text, res)
        return self


@dataclass
class Topic(Paged, UsesSession, _Indexed):
    """A class that represents a topic."""

    tid: int = None
    """The topic ID."""
    topic_name: str = None
    """The topic name."""
    pages: int = None
    """The amount of pages the topic has."""

    def __post_init__(self: Self) -> None:
        self.total_pages = 0

    def update_get(self: Self) -> Self:
        """GET this topic on the specified :py:ivar:`tid`."""
        page = self.get_page()
        # Update my own fields
        last_item = page.hierarchy[-1]
        last_name, _last_url = last_item
        self.topic_name = last_name
        self.pages = page.total_pages
        return self

    def get_page(self: Self, page: int = 1) -> Page["Message"]:
        """Gets a page of posts."""
        check_fields(self, "tid")
        res = api.get_topic_page(
            self.session, self.tid, (page - 1) * api.TOPIC_PER_PAGE
        )
        parsed = forum_parser.parse_page(
            res.text,
            forum_parser.parse_topic_content
        )
        if page != parsed["current_page"]:
            warn(f"Expected page {page}, got page {parsed['current_page']}")
        # just in case update_get() hasn't been called
        last_item = parsed["hierarchy"][-1]
        last_name, _last_url = last_item
        return Page(**parsed, content_type=Message)

    def get_size(self: Self) -> int:
        return self.pages


@dataclass
class Message(UsesSession, _Indexed):
    """A class that represents a message.

    A message (usually called a post) is the smallest unit of a forum. It
    carries a string of text as the content of the message, consisting of
    text, images, links, etc. It also carries other metadata like date of
    post and the user that  posted this post.
    """
    tid: int = None
    mid: int = None
    subject: str = None
    date: str = None
    edited: str | None = None
    content: str = None
    user: User | UserData = None
    icon: str | PostIcons = None
    board_name: InitVar[str] = None
    bid: InitVar[int] = None

    def __post_init__(self: Self, board_name: str, bid: int) -> None:
        if type(self.user) is dict:
            self.user = User(**self.user)
        if type(self.icon) is str:
            self.icon = PostIcons(self.icon)

    def submit_post(self: Self) -> Self:
        """POST this message on the specified :py:ivar:`tid`."""
        check_fields(self, "tid")
        res = api.post_message(
            self.session, self.tid, self.content, self.subject, self.icon
        )
        forum_parser.check_errors(res.text, res)
        return self

    def update_get(self: Self) -> Self:
        """GET this message on the specified :py:ivar:`mid`."""
        check_fields(self, "mid")
        res = api.get_message_page(
            self.session, self.mid
        )
        forum_parser.check_errors(res.text, res)
        parsed = forum_parser.parse_page(
            res.text,
            forum_parser.parse_topic_content
        )
        post = filter(lambda x: x["mid"] == self.mid, parsed["contents"])
        try:
            post = next(post)
            self.__init__(**post)
        except StopIteration:
            raise RequestError("Requested post doesn't exist in page",
                               response=res)
        return self

    def submit_edit(self: Self, reason: str = "") -> Self:
        """POST an edit with a specified reason."""
        check_fields(self, "mid", "tid")
        res = api.edit_message(
            self.session, self.mid, self.tid, self.content, self.subject,
            self.icon, reason
        )
        forum_parser.check_errors(res.text, res)
        return self

    def update_quotefast(self: Self) -> Self:
        """GETs the BBC of message on the specified :py:ivar:`mid`.
        This uses the `quotefast` action."""
        check_fields(self, "mid")
        params = {
            "quote": str(self.mid),
            "xml": None,
            "modify": None,  # allows posts from closed topics
        }
        res = api.do_action(
            self.session, "quotefast", params=params,
            no_percents=True
        )
        if "<html" in res.text:  # this is not XML!
            forum_parser.check_errors(res.text, res)
        post = forum_parser.parse_quotefast(res.text)
        self.__init__(**post)
        return self


@dataclass(frozen=True)
class Search(UsesSession, Paged):
    """A class representing a search query.

    .. warning:: Searching takes quite a long time for some reason.
    Use sparingly."""

    query: str
    """The text to search for."""
    match: str | SearchType = SearchType.ALL_WORDS
    """The search criteria: either to match all words or any words."""
    user: str = "*"
    """Which user to search their posts, delimited with a comma.
    ``*`` means all users."""
    sort: str | SortBy = SortBy.RELEVANCE
    """The sorting criteria."""
    order: str | SortOrder = SortOrder.DESC
    """The ordering of the sort."""
    complete: bool = False
    """Whether to show the search result as a complete message."""
    subject_only: bool = False
    """Whether to search the subject only or not."""
    min_age: int = 0
    """The minimal age for posts in days."""
    max_age: int = 9999
    """The maximal age for posts in days."""
    forums: list[int] = field(
        default_factory=lambda: list((2, 3, 5, 6))
    )
    """A list of forum IDs to search."""
    # IDEA: Make this an enum?
    MSGS_PER_PAGE: ClassVar[int] = 30

    def __post_init__(self: Self) -> None:
        # Enum-ify!
        if type(self.match) is str:
            self.match = SearchType[self.match.lower()]
        if type(self.sort) is str:
            self.sort = SortBy[self.sort.lower()]
        if type(self.order) is str:
            self.order = SortOrder[self.order.lower()]

    def get_page(self: Self, page: int = 1) -> Page[Message]:
        # This uses the params query string to provide parameters.
        # Creation of this is based from this source code:
        # https://github.com/SimpleMachines/SMF/blob/release-2.1/Sources/Search.php#L996-L1016
        fields = {
            # We're assuming this is always 1
            # This is only used for one occasion
            # https://github.com/SimpleMachines/SMF/blob/release-2.1/Sources/Search.php#L364-L366
            "advanced": "1",
            "brd": ",".join(map(str, self.forums)),
            "sort": self.sort.value,
            "sort_dir": self.order.value,
            "search": self.query,
            "minage": str(self.min_age),
            "maxage": str(self.max_age),
        }
        if self.complete:
            fields["show_complete"] = ""
        if self.subject_only:
            fields["subject_only"] = ""
        # Convert
        params = '|"|'.join(
            key + "|'|" + value
            for key, value in fields.items()
        ).encode()
        params = zlib.compress(params)
        params = base64.b64encode(params)
        params = (params
                  .replace(b"+", b"-")
                  .replace(b"/", b"_")
                  .replace(b"=", b".")
                  )

        res = api.do_action(
            self.session, "search2", params={
                "params": params,
                "start": str((page - 1) * self.MSGS_PER_PAGE)
            },
            no_percents=True
        )
        forum_parser.check_errors(res.text, res)
        parsed = forum_parser.parse_page(
            res.text,
            forum_parser.parse_search_content
        )
        page = Page(**parsed, content_type=Message)
        # HACK: Cannot write into frozen instance normally
        object.__setattr__(self, "pages", page.total_pages)
        return page

    def get_size(self: Self) -> int:
        try:
            return self.pages
        except AttributeError:
            return None
