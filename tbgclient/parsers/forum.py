from bs4 import BeautifulSoup, NavigableString
from tbgclient.protocols.forum import (
    MessageData, PageData, UserData, AlertData, BoardData, TopicData
)
from tbgclient.exceptions import RequestError
import re
from typing import TypeVar, Callable
from requests import Response
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs
from functools import reduce
from warnings import warn

T = TypeVar('T')
date_format = "%b %d, %Y, %I:%M:%S %p"


def date_regex() -> str:
    return (
        date_format
        .replace("%b", r"\w+")
        .replace("%d", r"\d\d")
        .replace("%Y", r"\d\d\d\d")
        .replace("%I", r"\d\d")
        .replace("%M", r"\d\d")
        .replace("%S", r"\d\d")
        .replace("%p", r"(AM|PM)")
    )


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


def dl_to_dict(element: BeautifulSoup) -> dict[BeautifulSoup, BeautifulSoup]:
    """Turn a description list into a dictionary."""
    keys = [x for x in element.children if x.name == "dt"]
    values = [x for x in element.children if x.name == "dd"]
    return dict(zip(keys, values))


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
        errors_dt = errors.contents[1].contents[1].text
        errors_dd = errors.contents[1].contents[3]
        raise RequestError(
            f"{errors_dt.strip()}\n"
            + "\n".join(str(string).strip()
                        for string in errors_dd.contents[::2]),
            response=response
        )


def get_hidden_inputs(document: str) -> dict[str, str]:
    """Get hidden input values on a form.
    Useful if you want to find nonce values.

    :param document: The document.
    :type document: str"""
    doc = parser(document)
    form = doc.find_all("form")[1:]  # first one is always the search box
    if len(form) > 1:
        raise ValueError(
            "FIXME: Found more than 1 form\n"
            f"{[str(x) for x in form if x.clear() or True]}"
        )
    elif len(form) == 0:
        raise ValueError("FIXME: Is the search box form missing?")
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
        .find("li", {"class": re.compile(r"cust_gender")})
    )
    if poster_gender is not None:
        user["gender"] = (
            poster_gender
            .find("span")
            .get("title")
        )
    # website
    poster_website = user_info.find("li", {"class": "profile"})
    if poster_website is not None and poster_website.find("li") is not None:
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


def parse_topic_content(content: BeautifulSoup,
                        hierarchy: list[tuple[str, str]]) -> list[MessageData]:
    """Parse ``#content_section`` of a topic page.
    This is meant to be used with :py:func:`parse_page`.

    :param content: The ``#content_section`` element of the page.
    :type content: BeautifulSoup
    :return: A list of messages.
    :rtype: list[MessageData]
    """
    forum_posts = content.find("div", {"id": "forumposts"})
    messages = forum_posts.find_all("div", {"id": re.compile(r"msg\d+")})
    # Get the topic ID
    queries = {
        k: v[0]
        for _, link in hierarchy
        for k, v in parse_qs(urlparse(link).query).items()
    }
    tid = queries.setdefault('topic', '0')
    tid = int(tid.split(".")[0])
    return [
        {"tid": tid, **parse_message(msg)}
        for msg in messages
    ]


def parse_search_item(msg: BeautifulSoup) -> MessageData:
    """Parse a search item.

    :param msg: The message element.
    :type msg: BeautifulSoup
    :return: The parsed message.
    :rtype: MessageData
    """
    # We are assuming SMF can only search for posts
    # and not topics like in FluxBB.
    topic_details = msg.find("div", {"class": "topic_details"})
    location = topic_details.find("h5")
    smalltext = topic_details.find("span")
    content = msg.find("div", class_="list_posts")

    board_link = location.contents[0]
    topic_link = location.contents[2]
    user_link = smalltext.find("a")
    date_text = "".join(
        child
        for child in smalltext.children
        if isinstance(child, NavigableString)
    )
    date_text = datetime.strptime(
        re.search(date_regex(), date_text)[0],
        date_format
    )

    # board
    board_name = board_link.text
    board_link = urlparse(board_link.get("href"))
    bid = parse_qs(board_link.query)["board"][0].split(".")[0]
    # topic
    subject = topic_link.get("title")
    topic_link = urlparse(topic_link.get("href"))
    tid = parse_qs(topic_link.query)["topic"][0].split(".")[0]
    mid = int(topic_link.fragment[3:])
    # user
    username = user_link.text
    user_url = urlparse(user_link.get("href"))
    user_query = parse_qs(user_url.query)
    # Note the version difference:
    # Older version of Python may seperate ; as well as &
    # (meaning user_query will have "u")
    # This is no longer the case since 3.10
    if "u" in user_query:
        uid = user_query["u"]
    else:
        uid = parse_qs(user_query["action"][0], separator=";")["u"]

    return {
        "board_name": board_name,
        "bid": int(bid),
        "subject": subject,
        "tid": int(tid),
        "mid": mid,
        "user": {
            "name": username,
            "uid": int(uid[0])
        },
        "date": date_text,
        "content": (
            "".join(map(str, content.children)).strip()
            if content is not None
            else None
        ),
    }


def parse_search_content(
    content: BeautifulSoup,
    hierarchy: list[tuple[str, str]]
) -> list[MessageData]:
    """Parse ``#content_section`` of a search page.
    This is meant to be used with :py:func:`parse_page`.

    :param content: The ``#content_section`` element of the page.
    :type content: BeautifulSoup
    :return: A list of messages.
    :rtype: list[MessageData]
    """
    items = content.find_all("div", {"class": "windowbg"})
    return [parse_search_item(item) for item in items]


def parse_alerts_content(
    content: BeautifulSoup,
    hierarchy: list[tuple[str, str]]
) -> list[AlertData]:
    """Parse ``#content_section`` of an alert page.
    This is meant to be used with :py:func:`parse_page`.

    :param content: The ``#content_section`` element of the page.
    :type content: BeautifulSoup
    :return: A list of alerts.
    :rtype: list[MessageData]
    """
    patterns = {
        # tuple(re.split(r"(?={)|(?<=})|^|$", '...')[1:-1])
        "msg_quote": ('{user}', ' quoted you in ', '{msg}'),
        "msg_mention": ('{user}', ' mentioned you in ', '{msg}'),
        "board_topic": (
            '{user}', ' started a new topic, ',
            '{topic}', ', in ', '{board}'
        ),  # Is this ever a thing?
    }

    def parse_user_link(link: BeautifulSoup) -> UserData:
        """From a user link element, turn it into a UserData."""
        username = link.text
        user_url = urlparse(link.get("href"))
        user_query = parse_qs(user_url.query)
        # Note the version difference:
        # Older version of Python may seperate ; as well as &
        # (meaning user_query will have "u")
        # This is no longer the case since 3.10
        if "u" in user_query:
            uid = user_query["u"]
        else:
            uid = parse_qs(user_url.query, separator=";")["u"]
        return {
            "name": username,
            "uid": int(uid[0])
        }

    def parse_topic_link(link: BeautifulSoup) -> TopicData:
        """From a message link element, turn it into a TopicData."""

        topic_link = urlparse(link.get("href"))
        tid = parse_qs(topic_link.query)["topic"][0].split(".")[0]
        return {
            "tid": int(tid),
            "topic_name": link.text
        }

    def parse_message_link(link: BeautifulSoup) -> MessageData:
        """From a message link element, turn it into a MessageData."""
        topic_data = parse_topic_link(link)
        # The text of the link is parsed as topic_name
        # In messages, these are for subjects
        topic_data["subject"] = topic_data["topic_name"]
        del topic_data["topic_name"]
        msg_link = urlparse(link.get("href"))
        subject = link.get("title")
        mid = int(msg_link.fragment[3:])
        return {
            "subject": subject,
            "mid": mid,
            **topic_data,
        }

    def parse_board_link(link: BeautifulSoup) -> BoardData:
        board_name = link.text
        board_link = urlparse(link.get("href"))
        bid = parse_qs(board_link.query)["board"][0].split(".")[0]
        return {
            "board_name": board_name,
            "bid": int(bid),
        }

    group_parser = {
        "msg_quote": {
            "user": parse_user_link,
            "msg": parse_message_link,
        },
        "msg_mention": {
            "user": parse_user_link,
            "msg": parse_message_link,
        },
        "board_topic": {
            "user": parse_user_link,
            "topic": parse_topic_link,
            "board": parse_board_link,
        },
    }

    # Parse the alert text
    table = content.find("table", {"id": "alerts"})
    # print(table)
    result = []
    for row in table.find_all("tr"):
        alert_text = row.find("td", {"class": "alert_text"})
        alert_text = alert_text.find("div")
        # the element has trailing and leading spaces for some reason
        # completely unacceptable
        for pat_name, pat in patterns.items():
            if len(pat) != len(alert_text.contents):
                continue
            matched = {"type": pat_name, "values": {}}
            for rule, elm in zip(pat, alert_text.children):
                if rule.startswith("{") and rule.endswith("}"):
                    name = rule[1:-1]
                    matched["values"][name] = group_parser[pat_name][name](elm)
                elif rule != elm:
                    break  # not a match
            else:  # no break: we have a match!
                break
        else:  # no break: no patterns match
            matched = {"type": "unknown", "values": {"data": alert_text}}
            warn(
                f"Cannot parse alert {alert_text}\n"
                "Please make an issue and send a sample of this alert."
            )

        # Attach metadata
        # Date
        alert_time = row.find("td", {"class": "alert_time"})
        time = alert_time.find("time")
        time = int(time.get("datetime"))
        date = (
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            + timedelta(seconds=time)
        )
        # Alert ID
        alert_buttons = row.find("td", {"class": "alert_buttons"})
        button_url = urlparse(alert_buttons.find("a").get("href"))
        # This would be the delete button
        button_query = parse_qs(button_url.query)
        if "aid" in button_query:
            aid = button_query["aid"]
        else:
            aid = parse_qs(button_url.query, separator=";")["aid"]

        result.append({
            **matched,
            "date": date,
            "aid": int(aid[0]),
        })

    return result


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
    if pagelinks is None:  # can't find 'em!
        current_page = 0
        total_pages = 0
    else:
        pages = [
            x
            for x in pagelinks.contents if parse_integer(x.text) is not None
        ]
        current_page = int(
            pagelinks.find("span", {"class": "current_page"}).text
        )
        total_pages = parse_integer(pages[-1].text)
    # get content
    content = page_parser(content_section, hierarchy)

    return {
        "hierarchy": hierarchy,
        "current_page": current_page,
        "total_pages": total_pages,
        "contents": content
    }


def parse_quotefast(document: str) -> MessageData:
    """Parses the XML given by the `quotefast` action.

    :param document: The document.
    :return: The parsed message
    :rtype: MessageData
    """

    elm = xml_parser(document)
    subject = elm.find("subject")
    message = elm.find("message")
    reason = elm.find("reason")

    edit_time = int(reason.get("time"))
    if edit_time == 0:
        edit_time = None
    else:
        edit_time = datetime.fromtimestamp(edit_time, timezone.utc)

    return {
        "subject": subject.text,
        "content": message.text,
        "mid": parse_integer(message.get("id")[4:]),
        "edited": edit_time
    }


def parse_profile(document: str) -> UserData:
    """Parses the given user profile page.
    :param document: The document.
    :type document: str
    :return: The parsed profile.
    :rtype: UserData
    """
    elm = parser(document)
    profile_view = elm.find("div", {"id": "profileview"})

    result: UserData = {}

    canonical_link = elm.find("link", {"rel": "canonical"})
    profile_link = urlparse(canonical_link.get("href"))
    uid = parse_qs(profile_link.query, separator=";")["u"]
    result["uid"] = int(uid[0])

    basic_info = profile_view.find("div", {"id": "basicinfo"})
    # username
    username = basic_info.find("div", class_="username")
    group = username.find("span", class_="position")
    result["group"] = group.text
    group.decompose()
    result["name"] = username.text.strip()
    # avatar
    avatar = basic_info.find("img", class_="avatar")
    if avatar is not None:
        result["avatar"] = avatar.get("src")
    # icon_fields
    icon_fields = basic_info.find("ul", class_="icon_fields")
    result["website"] = icon_fields.find("span", class_="www")
    if result["website"] is not None:
        result["website"] = result["website"].parent.get("href")
    result["gender"] = icon_fields.find("span", class_=re.compile("^gender"))
    if result["gender"] is not None:
        result["gender"] = result["gender"].get("title")

    detailed_info = profile_view.find("div", {"id": "detailedinfo"})
    detailed_dict = reduce(dict.__or__, (
        dl_to_dict(dl)
        for dl in detailed_info.find_all("dl")
    ), {})
    # Map the terms into dictionary keys
    mapping = {
        # None means discard
        # All that's not listed here will become social info
        "Username:": None,
        "Posts:": "posts",
        "Email:": "email",
        "Personal text:": "blurb",
        "Age:": None,
        "Real name:": "real_name",
        "From:": "location",
        # IDEA: add these fields?
        "Date registered:": None,
        "Local Time:": None,
        "Last active:": None,
    }
    result["social"] = {}
    for dt, dd in detailed_dict.items():
        key = dt.text.strip()
        if key in mapping:
            if mapping[key] is not None:
                result[mapping[key]] = dd.text
        else:
            result["social"][key[:-1]] = dd.text
    result["posts"] = parse_integer(result["posts"].split()[0])
    # signature
    signature = profile_view.find("div", class_="signature")
    signature_title = signature.find("h5", text="Signature:")
    signature_title.decompose()
    result["signature"] = str(signature)

    return result
