import requests
from typing import Self


class RequestError(Exception):
    """An exception that is raised when an API call failed, either by a
    failure response code or if an API call cannot be processed further.

    This exception provides the response causing the exception, accessable in
    the attribute :py:attr:`response`.
    """

    response: requests.Response
    """The response that caused the exception."""
    def __init__(self: Self, *args, response: requests.Response) -> None:
        super().__init__(*args)
        self.response = response


class IncompleteError(Exception):
    """Called when an object cannot execute a function due to an undefined
    instance variable."""
    def __init__(self: Self, missing: str) -> None:
        super().__init__(f"{', '.join(missing)} not specified")
        self.missing = missing
