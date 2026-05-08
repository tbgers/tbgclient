"""
Miscellaneous utilities for this module.
"""
from dataclasses import fields
from warnings import warn
from typing import Any, Iterator
from collections.abc import Mapping
try:
    # PORT: 3.10 and below doesn't have typing.Self
    from typing import Self
except ImportError:
    from typing_extensions import Self


def _check_field_names(self: Any) -> None:
    if "__field_names__" not in dir(self):
        self.__field_names__ = tuple(x.name for x in fields(self))


class Data(Mapping):
    """Base class for all data classes used by ``tbgclient``."""

    def __init_subclass__(cls: Any) -> None:
        # set the annotated attributes to None so that it's optional
        # apparently __annotations__ is still used on 3.14?
        annotations = cls.__annotations__
        for k in annotations.keys():
            setattr(cls, k, getattr(cls, k, None))

    # implement methods required by Mapping
    # since these classes used to be dicts
    def __getitem__(self: Self, name: str) -> None:
        _check_field_names(self)
        if name not in self.__field_names__:
            raise KeyError(name)
        return getattr(self, name)

    def __setitem__(self: Self, name: str, value: Any) -> None:
        _check_field_names(self)
        if name not in self.__field_names__:
            warn(
                f"Trying to write into {name} on {type(self).__name__};"
                " this might be unintended"
            )
        return setattr(self, name, value)

    def __iter__(self: Self) -> Iterator[str]:
        _check_field_names(self)
        return iter(self.__field_names__)

    def __len__(self: Self) -> int:
        _check_field_names(self)
        return len(self.__field_names__)
