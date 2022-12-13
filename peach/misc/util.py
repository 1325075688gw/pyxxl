import decimal
import typing
from datetime import datetime
from enum import Enum
from typing import Type, Any, Union

from dacite import from_dict, Config
from peach.misc import dt
from dataclasses import asdict


def dict_to_dto(data: typing.Dict, data_class: Type) -> Any:
    return from_dict(
        data_class=data_class,
        data=data,
        config=Config(
            cast=[Enum, decimal.Decimal],
            type_hooks={
                datetime: lambda t: dt.from_timestamp(int(int(t) / 1000)),
                int: int,
            },
        ),
    )


def dto_to_dict(data_class: Union[Type, None]) -> dict:
    if data_class is None:
        return None
    return asdict(data_class)


def qdict_to_dict(qdict):
    """Convert a Django QueryDict to a Python dict.

    Single-value fields are put in directly, and for multi-value fields, a list
    of all values is stored at the field's key.

    """
    return {k: v[0] if len(v) == 1 else v for k, v in qdict.lists()}


def singleton(cls):
    """singleton decorator"""
    instance = {}

    def _singleton(*args, **kw):
        if cls not in instance:
            instance[cls] = cls(*args, **kw)
        return instance[cls]

    return _singleton
