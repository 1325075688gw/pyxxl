import typing
from datetime import datetime
from enum import Enum
from typing import Type, Any

from dacite import from_dict, Config
from peach.misc import dt


def dict_to_dto(data: typing.Dict, data_class: Type) -> Any:
    return from_dict(
        data_class=data_class,
        data=data,
        config=Config(
            cast=[Enum],
            type_hooks={
                datetime: lambda t: dt.from_timestamp(int(int(t) / 1000)),
                int: int,
            },
        ),
    )


def qdict_to_dict(qdict):
    """Convert a Django QueryDict to a Python dict.

    Single-value fields are put in directly, and for multi-value fields, a list
    of all values is stored at the field's key.

    """
    return {k: v[0] if len(v) == 1 else v for k, v in qdict.lists()}


def singleton(cls, *args, **kw):
    """singleton decorator"""
    instance = {}

    def _singleton():
        if cls not in instance:
            instance[cls] = cls(*args, **kw)
        return instance[cls]

    return _singleton
