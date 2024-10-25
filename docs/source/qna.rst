=====================
Questions and Answers
=====================

Programming
===========
When I tried to make a request, it says ``"No default session is defined"``.
----------------------------------------------------------------------------
..
    I've defined my logged-in session, but tbgclient doesn't use it! 

Try encasing your request with the ``with`` statement:

.. code-block:: python

    session = Session()
    with session:
        msg = Message(pid=152062).update_get()

Alternatively, you can set a default session with :py:func:`make_default`:

.. code-block:: python

    session = Session()
    session.make_default()
    msg = Message(pid=152062).update_get()

Miscellaneous
=============
Why did you rewrite ``tbgclient``?
----------------------------------

`Mind the history lesson here, I'm not quite sure how to answer...`

``tbgclient`` was an extension of the earlier `TBGScraper`_, a tool that only has one purpose and that is scraping TBG
pages. This is made on the time where I don't really know how to write neat, readable code, meaning that developing it 
essentially requires a really large prior knowledge on how the code works to develop it. Eventually, the code becomes
so messy that I deemed it to be impenetrable. 

In the end, the TBGs migrated to SMF, making the older ``tbgclient`` not work anymore as the architecture is vastly
different, so a rewrite is needed anyway.

.. _TBGScraper: https://github.com/tbgers/tbg-scraper/