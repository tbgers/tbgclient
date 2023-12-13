import requests


class RequestError(Exception):
    """An exception that is raised when an API call failed, either by a 
    failure response code or if an API call cannot be processed further.

    This exception provides the response causing the exception, accessable in 
    the attribute ``response``.

    :ivar response: The response that caused the exception.
    """
    def __init__(self, *args, response: requests.Response):
        super().__init__(*args)
        self.response = response


class IncompleteError(Exception):
    """Called when an object cannot execute a function due to an undefined 
    instance variable."""
    pass
