"""
Parsing utilities for the TBGs chat.
"""

from tbgclient.data.chat import UserData, ResponseData, MessageData
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime as parse_date


def parse_response(response: str) -> ResponseData:
    """Parse the response given by the TBGs chat server.

    :param response: The response content.
    :type response: str
    """
    document = BeautifulSoup(response, features="xml")

    # Parse the info, if it exists.
    infos = {}
    for info in document.find("infos").children:
        infos[info.get("type")] = info.contents[0]

    # Parse the online users list.
    users = []
    if (elm := document.find("users")) is not None:
        for user in elm.children:
            users.append(UserData(
                uid=int(user["userID"]),
                role=user["userRole"],
                name=user.contents[0],
            ))

    # Parse the messages.
    messages = []
    if (elm := document.find("messages")) is not None:
        for message in elm.children:
            username, text = message.contents
            messages.append(MessageData(
                mid=int(message["id"]),
                date=parse_date(message["dateTime"]),
                user=UserData(
                    uid=int(message["userID"]),
                    role=message["userRole"],
                    name=username.contents[0],
                ),
                cid=int(message["channelID"]),
                content=text.contents[0]
            ))

    return ResponseData(
        infos=infos,
        users=users,
        messages=messages,
    )
