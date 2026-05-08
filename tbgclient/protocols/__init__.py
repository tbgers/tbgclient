"""
Contains protocols and such that ``tbgclient`` uses.

This is similar to how some Java or C# devs would use and organize their
interfaces.
It might seem weird to see this on a Python module (and it is), but linters
love these stuff.

.. deprecated:: 0.7
    Use :py:mod:`tbgclient.data` instead.
"""

from warnings import warn

from tbgclient.data import chat, forum

warn("tbgclient.protocols is deprecated and will be removed in 1.0;"
     " use tbgclient.data instead", DeprecationWarning)

__all__ = ["chat", "forum"]
