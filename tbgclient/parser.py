from bs4 import BeautifulSoup
from .protocols.forum import *
import re
from typing import TypeVar, Callable

T = TypeVar('T')


parser_config = dict(
    features = "html.parser",  # using html.parser
)


def parse_integer(text: str) -> int:
    return int(re.sub(r"[^\d]", "", text))


def parser(*args, **kwargs) -> BeautifulSoup:
    """Convenience function for ``BeautifulSoup(..., **parser_config)``."""
    return BeautifulSoup(*args, **parser_config, **kwargs)


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
    poster_gender = user_info \
                        .find("li", {"class": "im_icons"}) 
    if poster_gender is not None:
        user["gender"] = poster_gender \
                            .find("li", {"class": re.compile(r"cust_gender")}) \
                            .find("span") \
                            .get("title")
    # website
    poster_website = user_info.find("li", {"class": "profile"})
    if poster_website is not None:
        user["website"] = poster_website \
                            .find("li") \
                            .find("a") \
                            .get("href")
    # location
    poster_location = user_info.find("li", {"class": re.compile(r"cust_loca")})
    if poster_location is not None:
        user["location"] = poster_location.text[6:]

    content = wrapper.find("div", {"class": "post"}).find("div")
    signature = wrapper \
                    .find("div", {"class": "moderatorbar"}) \
                    .find("div", {"class": "signature"})
    if signature is not None:
        user["signature"] = "".join(map(str, signature.children)).strip()

    return {
        "mid": mid,
        "content": "".join(map(str, content.children)).strip(),
        "user": user
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
    :return: The parsed page.
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
        "contents": content
    }
