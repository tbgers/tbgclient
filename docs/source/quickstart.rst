===========
Quick start
===========

This guides assumes you know how to use Python. If you haven't, have look at the `Python tutorial`_ first.

.. important::
    It's *strongly* recommended to learn the language first before you use libraries like tbgclient. This 
    `Scratch project`_ explains why doing the opposite is a bad idea.

.. _Python tutorial: https://docs.python.org/3/tutorial/
.. _Scratch project: https://scratch.mit.edu/projects/842407135/


.. _quickstart-get-message: 

Retrieving messages
===================

Retrieving messages can be done by the :py:func:`~tbgclient.Message.update_get()` function.

.. code-block:: python
    
    from tbgclient import Message
    msg = Message().update_get(mid=152062)

If you have a session defined, you can use the convenient :py:func:`~tbgclient.Session.get_message()` function.
This will also wrap the object in a session context.

.. code-block:: python

    from tbgclient import Session
    session = Session()
    msg = session.get_message(mid=152062)


.. _quickstart-session:

Sessions
========

To do actions under a specific user, you can make a session object. You can have multiple sessions in one script.

.. code-block:: python

    from tbgclient import Session
    session1 = Session()
    session1.login("username1", "password1")
    session2 = Session()
    session2.login("username2", "password2")

There are two ways to specify which session to use. One uses the ``with`` statement:

.. code-block:: python

    with session1:
        Message(content="Hello, world!").submit_post(tid=170)

Another is to make a session context, using the :py:func:`~tbgclient.session.UsesSession.using()` function.

.. code-block:: python

    (
        Message(content="Hello, world!")
        # This function wraps the message in a session context
        .using(session2)  
        .submit_post(tid=170)
    )


.. _quickstart-default-session:

Default session
---------------

When no session is specified, whether by the ``with`` statement or by a session context, the default session is used instead.
This session has no authentication data; it is equivalent to a logged-out user. 

The default session is stored at :py:data:`~tbgclient.session.default_session`, though it is recommended to replace it with 
the :py:class:`~tbgclient.session.Session` you made, instead of doing operations directly on the initial default session.

.. code-block:: python
    
    from tbgclient import Session
    session = Session()
    session.login("username", "password")
    session.make_default()
