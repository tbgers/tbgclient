from bs4 import BeautifulSoup
from .protocols.forum import *
import re
from typing import TypeVar, Callable

T = TypeVar('T')


parser_config = dict(
    features = "html.parser",  # using html.parser
)


def parser(*args, **kwargs) -> BeautifulSoup:
    """Convenience function for ``BeautifulSoup(..., **parser_config)``."""
    return BeautifulSoup(*args, **parser_config, **kwargs)


def parse_message(msg: BeautifulSoup) -> MessageData:
    """Parse a message.

    :param msg: The message element
    :type msg: BeautifulSoup
    :return: The parsed message.
    :rtype: MessageData
    """
    mid = int(msg.attrs["id"][3:])
    wrapper = msg.find("div", {"class": "post_wrapper"})
    poster = wrapper.find("div", {"class": "poster"})
    # TODO: parse poster
    content = wrapper.find("div", {"class": "post"}).find("div")

    return {
        "mid": mid,
        "content": str(content)
    }



def parse_topic_content(content: BeautifulSoup) -> list[MessageData]:
    """Parse ``#content_section`` of a topic page.

    :param content: The ``#content_section`` element of the page.
    :type content: BeautifulSoup
    :return: A list of messages.
    :rtype: list[MessageData]
    """
    forum_posts = content.find("div", {"id": "forumposts"})
    messages = forum_posts.find_all("div", {"id": re.compile("msg\d+")})
    return [parse_message(msg) for msg in messages]


def parse_page(doc: str, page_parser: Callable[[BeautifulSoup], list[dict]]) -> PageData:
    """Parse a single page.

    :param doc: The document.
    :type doc: str
    :return: The page
    :rtype: dict
    """
    elm = parser(doc)
    # get hierarchy
    navbar = elm.find("div", {"class": "navigate_section"})
    hierarchy = [
        (x.text.strip("► \n"), x.contents[-2].attrs["href"])
        for x in navbar.find_all("li")
    ]
    # get current page
    content_section = elm.find("div", {"id": "content_section"})
    pagelinks = content_section.find("div", {"class": re.compile("pagelinks")})
    pages = [*pagelinks.find_all("a", {"class": "nav_page"})]
    current_page = int(pagelinks.find("span", {"class": "current_page"}).text)
    total_pages = pages[-1].text
    if total_pages == "":
        total_pages = pages[-2].text
    # get content
    content = page_parser(content_section)
    
    return {
        "hierarchy": hierarchy,
        "current_page": current_page,
        "total_pages": total_pages,
        "content": content
    }
