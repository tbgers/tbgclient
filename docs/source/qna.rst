=====================
Questions and Answers
=====================


Programming
===========
.. _qna-default-session:

I've defined my logged-in session, but tbgclient doesn't use it! 
----------------------------------------------------------------

Try setting it as a default session with :py:func:`~tbgclient.Session.make_default()`:

.. code-block:: python

    session = Session()
    session.make_default()
    msg = Message(pid=152062).update_get()

Alternatively, you can encase your request with the ``with`` statement:

.. code-block:: python

    session = Session()
    with session:
        msg = Message(pid=152062).update_get()


Design
======
.. _qna-session-in-object:

Why doesn't tbgclient work like scratchattach? Why the forum classes?
---------------------------------------------------------------------
`scratchattach`_ (and others like it) allows the session to create the object it needs, passing itself to the object
for the created object to refer on later.

.. code-block:: python
    
    import scratchattach as sa
    session = sa.login("username", "password")
    topic = session.connect_topic(603418)

By doing so, objects will have to *store* the session somewhere, and that doesn't seem right to me.

Forum classes are supposed to be abstractions of the elements in the TBGs. :py:class:`~tbgclient.forum.Message`
is supposed to represent messages, :py:class:`~tbgclient.forum.User` represents users, etc. Sessions have no place
in these classes, so obviously they don't store them. This is made more serious by the fact that all the classes
are dataclasses as well. [#dc_initvar]_

For the sake of the argument, say that the classes *do* store the creator session. (Incidentally, this is the approach
that the older `tbgclient-legacy`_ uses.) There are problems with this approach:

* When an object is created, they have to specify the session to use. From experience of developing tbgclient-legacy, 
  this act turned into a massive, unnecessary chore, especially since the objects have to pass in what would most 
  likely be the same, single session for this one script.
* An object storing something opaquely could bring unexpected behaviour. What should be done with this session could
  be done with another session, just because the other is their creator. I know DIs are one useful pattern, but for
  a loose dependency like this, it's only a burden that's asking for trouble. Explicit is better than implicit.
* Serialization could be a problem. If a post has to be stored and retrieved, the session is lost along the way
  (since it has no reason to be stored) and has to be provided. It would be easier and nicer if the class reflects 
  this limitation. After all, this was part of a mass forum scraper, and that fact hasn't changed until now.

To solve this issue, I implemented the :py:class:`~tbgclient.session.UsesSession` mixin. Anything that needs a session 
could retrieve the current one by the implemented :py:attr:`~tbgclient.session.UsesSession.session` property. This 
also means the process of getting the current session is delegated to this class. Creating objects becomes much easier.
As for the sessions, they are stored in a shared session context, so other objects (that bases 
:py:class:`~tbgclient.session.UsesSession`) don't have to store them. This also makes serialization easier.

This solution works, but not completely watertight. Having a global state is generally a big no-no for various reasons
(if you read this, you should already know that). tbgclient does its best to alleviate this, by distinguishing context
by the thread, event loop, and process; and including a self-destructing check if something may have tampered the
stack. [#self_destruct]_ 

On a more serious note, this means the way of updating and submitting objects is completely different than libraries
like scratchattach. Instead of doing it all from the session, you have to make the object first, then call the object's
function. An equivalent tbgclient code of the scratchattach example above would look something like this:

.. code-block:: python

    from tbgclient import Topic, Session
    session = Session().login("username", "password")
    with session:
        topic = Topic(tid=170).update()

If this really bothers you, there are :doc:`convenience functions <convenience>` in the tbgclient module. 
These functions could be much more straightforward to read for programmers familiar with scratchattach and alike.

.. _scratchattach: https://github.com/TimMcCool/scratchattach
.. [#dc_initvar]

    You could annotate the dataclass so the session attribute is an :py:class:`~dataclasses.InitVar`, but that doesn't 
    eradicate the problem that the object still stores the session somewhere.

.. _tbgclient-legacy: https://github.com/tbgers/tbgclient-legacy
.. [#self_destruct]

    If you see an error related to the context system, either something is abusing it, or there's a bug in my code.
    In either case, do tell!


.. _qna-no-bot-class:

tbgclient seems too lean. Why isn't there some class that makes bots?
-------------------------------------------------------------------------
tbgclient was supposed to be a library, not a framework. While the purpose of tbgclient is automation, it's not
about making this or that specific bot. I made it to be a general-use TBGs scraper library; after all, this was once
a tool to scrape the entirety of the forums.


Miscellaneous
=============
.. _qna-rewrite:

Why did you rewrite tbgclient?
----------------------------------

*Mind the history lesson here, I'm not quite sure how to answer...*

tbgclient was an extension of the earlier `TBGScraper`_, a tool that only has one purpose and that is scraping TBG
pages. This is made on the time where I don't really know how to write neat, readable code, meaning that developing it 
essentially requires a really large prior knowledge on how the code works to develop it. Eventually, the code becomes
so messy that I deemed it to be impenetrable. 

In the end, the TBGs migrated to SMF, making the older tbgclient not work anymore as the architecture is vastly
different, so a rewrite is needed anyway.

.. _TBGScraper: https://github.com/tbgers/tbg-scraper/