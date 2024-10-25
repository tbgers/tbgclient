from bs4 import BeautifulSoup
from tbgclient.protocols.forum import MessageData, PageData, UserData
from tbgclient.exceptions import RequestError
import re
from typing import TypeVar, Callable
from requests import Response
from datetime import datetime

T = TypeVar('T')
date_format = "%b %d, %Y, %I:%M:%S %p"


parser_config = dict(
    features="html.parser",  # using html.parser
)


def parse_integer(text: str) -> int | None:
    text = re.sub(r"[^\d]", "", text)
    if text == "":
        return None
    return int(text)


def parser(*args, **kwargs) -> BeautifulSoup:
    """Convenience function for ``BeautifulSoup(..., **parser_config)``."""
    return BeautifulSoup(*args, **parser_config, **kwargs)


def xml_parser(*args, **kwargs) -> BeautifulSoup:
    """Convenience function for
    ``BeautifulSoup(..., features="xml", **parser_config)``."""
    kwargs = {**parser_config, **kwargs, "features": "xml"}
    return BeautifulSoup(*args, **kwargs)


def check_errors(document: str, response: Response) -> None:
    """Checks for an error message in this document.

    :param document: The document.
    :type document: str
    :param response: The response to be supplied for :py:class:`RequestError`.
    :raises RequestError: An error message is found.
    """
    elm = parser(document)

    fatal_error = elm.find("div", {"id": "fatal_error"})
    if fatal_error is not None:
        message = fatal_error.contents[3] \
                             .contents[1]
        raise RequestError(
            f"An error has occurred: \n{message.text.strip()}\n"
            f"({message.get('id')})",
            response=response
        )
    errors = elm.find("div", {"id": "errors"})
    if errors is not None:
        errors_dt = errors.contents[0].text
        errors_dd = errors.contents[0].contents[1]
        raise RequestError(
            f"{errors_dt}: \n"
            + "\n".join(str(string) for string in errors_dd.contents[::2]),
            response=response
        )


def get_hidden_inputs(document: str) -> dict[str, str]:
    """Get hidden input values on a form.
    Useful if you want to find nonce values.

    :param document: The document.
    :type document: str"""
    doc = parser(document)
    form = doc.find_all("form")[1:]  # first one is always the search box
    if len(form) != 1:
        raise ValueError(
            "FIXME: Found more than 1 form\n"
            f"{[str(x) for x in form if x.clear() or True]}"
        )
    inputs = form[0].find_all("input", {"type": "hidden"})
    # filter elements that is not hidden
    nonce = {
        tag.get("name"): tag.get("value")
        for tag in inputs
    }
    return nonce


def parse_message(msg: BeautifulSoup) -> MessageData:
    """Parse a message.

    :param msg: The message element.
    :type msg: BeautifulSoup
    :return: The parsed message.
    :rtype: MessageData
    """
    mid = int(msg.attrs["id"][3:])
    wrapper = msg.find("div", {"class": "post_wrapper"})

    poster = wrapper.find("div", {"class": "poster"})
    edited = wrapper.find("span", {"class": "modified"})
    edited = edited.text[11:].strip()  # strip "Last Edit:"
    if edited == "":
        edited = None

    user: UserData = {}
    poster_title = poster.find("h4").find("a")
    user["name"] = poster_title.text
    # commence user_info...
    user_info = poster.find("ul", {"class": "user_info"})
    # avatar
    poster_avatar = user_info.find("li", {"class": "avatar"})
    if poster_avatar is not None:
        user["avatar"] = poster_avatar.find("img").get("src")
    # user group
    poster_group = user_info.find("li", {"class": "postgroup"})
    if poster_group is not None:
        user["group"] = poster_group.text
    # post count
    poster_activity = user_info.find("li", {"class": "postcount"})
    if poster_activity is not None:
        user["posts"] = parse_integer(poster_activity.text[7:])
    # blurb
    poster_blurb = user_info.find("li", {"class": "blurb"})
    if poster_blurb is not None:
        user["blurb"] = poster_blurb.text
    # gender
    poster_gender = (
        user_info
        .find("li", {"class": "im_icons"})
    )
    if poster_gender is not None:
        user["gender"] = (
            poster_gender
            .find("li", {"class": re.compile(r"cust_gender")})
            .find("span")
            .get("title")
        )
    # website
    poster_website = user_info.find("li", {"class": "profile"})
    if poster_website is not None:
        user["website"] = (
            poster_website
            .find("li")
            .find("a")
            .get("href")
        )
    # location
    poster_location = user_info.find("li", {"class": re.compile(r"cust_loca")})
    if poster_location is not None:
        user["location"] = poster_location.text[6:]

    post_info = wrapper.find("div", {"class": "postinfo"})
    icon = (
        post_info.find("span", {"class": "messageicon"}).find("img")
        .get("src")
    )
    # get the icon name
    icon = icon.split("/")[-1].split(".")[0]
    post_title = post_info.find("a", {"class": "smalltext"})
    content = wrapper.find("div", {"class": "post"}).find("div")
    signature = wrapper.find("div", {"class": "moderatorbar"}) \
                       .find("div", {"class": "signature"})
    if signature is not None:
        user["signature"] = "".join(map(str, signature.children)).strip()

    return {
        "mid": mid,
        "content": "".join(map(str, content.children)).strip(),
        "edited": edited,
        "user": user,
        "icon": icon,
        "date": datetime.strptime(post_title.text, date_format),
        "subject": post_title.get("title")
    }


def parse_topic_content(content: BeautifulSoup) -> list[MessageData]:
    """Parse ``#content_section`` of a topic page.

    :param content: The ``#content_section`` element of the page.
    :type content: BeautifulSoup
    :return: A list of messages.
    :rtype: list[MessageData]
    """
    forum_posts = content.find("div", {"id": "forumposts"})
    messages = forum_posts.find_all("div", {"id": re.compile(r"msg\d+")})
    return [parse_message(msg) for msg in messages]


def parse_page(document: str, page_parser: Callable[[BeautifulSoup],
               list[T]]) -> PageData[T]:
    """Parse a single page.

    :param document: The document.
    :type document: str
    :param page_parser: How to parse the page.
    :return: The parsed page.
    :rtype: dict
    """
    elm = parser(document)
    # get hierarchy
    navbar = elm.find("div", {"class": "navigate_section"})
    hierarchy = [
        (x.text.strip("► \n"), x.contents[-2].attrs["href"])
        for x in navbar.find_all("li")
    ]
    # get current page
    content_section = elm.find("div", {"id": "content_section"})
    pagelinks = content_section.find("div", {"class": re.compile("pagelinks")})
    pages = [
        x
        for x in pagelinks.contents if parse_integer(x.text) is not None
    ]
    current_page = int(pagelinks.find("span", {"class": "current_page"}).text)
    total_pages = parse_integer(pages[-1].text)
    # get content
    content = page_parser(content_section)

    return {
        "hierarchy": hierarchy,
        "current_page": current_page,
        "total_pages": total_pages,
        "contents": content
    }
