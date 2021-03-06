"""An implementation of users other than yourself."""


class User:
    """An object that defines a user other than yourself.

    Parameters
    ----------
    uID: int
        The user ID number.
    username: str, tbgclient.User
        The user username.
    title: str
        The type of user (New TBGer, TBG Team, etc.)
    location: str
        The location of user.
    website: str
        The website of user.
    signature: str
        The signature of user.
    realname: str
        The real name of user.
    postcount: int
        Amount of posts the user has posted.
    social: dict
        Social info of the user.
    flags: tbgclient.Flags
        Flags for the user. See tbgclient.Flags for more information.
    """
    uID: int
    username: str
    password: str
    title: str = None
    location: str = None
    website: str = None
    signature: str
    realname: str = None
    postCount: int
    social: dict = {}
    session = None

    def __init__(self, **data):
        self.__dict__.update(data)

    def __str__(self):
        return self.username

    def __repr__(self):
        return f"User(username={repr(self.username)},uID={repr(self.uID)})"

    def update(self):
        if self.session is not None:
            self.password = self.session.password

    def to_session(self):
        """Casts User to TBGSession."""
        if self.session is not None:
            return self.session
        else:
            return