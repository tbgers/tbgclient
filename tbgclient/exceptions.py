import requests


class RequestError(Exception):
    """An exception that is raised when an API call failed.

    :ivar response: The response that caused the error.
    """
    def __init__(self, *args, response: requests.Response):
        super.__init__(*args)
        self.response = response
