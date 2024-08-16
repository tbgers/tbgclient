tbgclient-rewritten
===================

    This module is severely unfinished and is only here so that I had a remote.
    Please don't try to use this yet; you'll only get disappointed.

Provides a way to get, post, and modify posts on the TBGs.

Example
-------
::
    from tbgclient import Session, Message

    session = Session()
    session.login("username", "password")
    with session:
        msg = Message(content="Test", tid=170)
        msg.submit_post()

