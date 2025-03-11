"""
Parsing utilities for the TBGs chat.
"""

from tbgclient.protocols.chat import ResponseData
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime as parse_date


def parse_response(response: str) -> ResponseData:
    document = BeautifulSoup(response, features="xml")
    print(document)

    # Parse the info, if it exists.
    infos = {}
    for info in document.find("infos").children:
        infos[info.get("type")] = info.contents[0]

    # Parse the online users list.
    users = []
    for user in document.find("users").children:
        users.append({
            "uid": int(user["userID"]),
            "group": user["userRole"],
            "name": user.contents[0],
        })

    # Parse the messages.
    messages = []
    for message in document.find("messages").children:
        username, text = message.contents
        messages.append({
            "mid": int(message["id"]),
            "date": parse_date(message["dateTime"]),
            "user": {
                "uid": int(username["userID"]),
                "group": username["userRole"],
                "name": username.contents[0],
            },
            "cid": int(message["channelID"]),
            "content": text.contents[0]
        })

    return {
        "infos": infos,
        "users": users,
        "messages": messages,
    }
