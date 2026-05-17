"""
Miscellaneous utilities for this module.
"""
from dataclasses import fields, is_dataclass, InitVar, field
from warnings import warn
from typing import Any, Iterator, Union, get_origin, get_args
from types import UnionType
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
        # better than having to make this a dataclass
        cls.__annotations__.update(Data.__annotations__)
        # set the annotated attributes to None so that it's optional
        # apparently __annotations__ is still used on 3.14?
        annotations = cls.__annotations__
        for k in annotations.keys():
            setattr(cls, k, getattr(cls, k, None))

    # allow dataclasses to cast other dataclasses that bases from them
    value: InitVar = field(kw_only=False, default=None)

    def __post_init__(self: Self, value: Any = None) -> None:
        if value is None:
            return
        if is_dataclass(value) and type(value) in type(self).__mro__:
            for fld in fields(value):
                name = fld.name
                # use object.__setattr__ in case the dataclass is frozen
                object.__setattr__(self, name, getattr(value, name))
        else:
            raise TypeError(
                f"cannot cast non-related {type(value).__name__!r} object"
                f" into {type(self).__name__}"
            )

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

    def __setattr__(self: Self, name: str, value: Any) -> None:
        if "__field_types__" not in dir(self):
            object.__setattr__(self, "__field_types__", {
                x.name: x.type for x in fields(self)
            })
        # try to cast the values into the designated types
        if value is not None:
            target = self.__field_types__.get(name, Any)
            origin = get_origin(target)
            if target is Any:
                pass
            elif origin is Union or origin is UnionType:
                excs = []
                types = get_args(target)
                if not (
                    Any in types
                    # no point trying to cast this value if above is the case
                    or any(isinstance(value, t) for t in types)
                ):
                    for t in types:
                        try:
                            value = t(value)
                            break
                        except Exception as e:
                            excs.append(e)
                            pass
                    else:
                        raise ExceptionGroup(
                            f"Cannot cast value {value} to {target}",
                            excs
                        )
            elif origin is not None and not isinstance(value, origin):
                try:
                    value = origin(value)
                except Exception as e:
                    raise TypeError(
                        f"Cannot cast value {value} to {origin}"
                    ) from e
            elif origin is None and not isinstance(value, target):
                try:
                    value = target(value)
                except Exception as e:
                    raise TypeError(
                        f"Cannot cast value {value} to {target}"
                    ) from e
        object.__setattr__(self, name, value)

    def __iter__(self: Self) -> Iterator[str]:
        _check_field_names(self)
        return iter(self.__field_names__)

    def __len__(self: Self) -> int:
        _check_field_names(self)
        return len(self.__field_names__)
