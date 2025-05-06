tbgclient
=========

Provides a way to get, post, and modify posts on the TBGs.

Example
-------
.. code-block:: python
    
    from tbgclient import Session, Message

    session = Session()
    session.login("username", "password")
    with session:
        msg = Message(content="Test", tid=170)
        msg.submit_post()

