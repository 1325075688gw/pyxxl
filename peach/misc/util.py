import typing
from datetime import datetime
from enum import Enum
from typing import Type, Any

from dacite import from_dict, Config
from peach.misc import dt


def dict_to_dto(msg: typing.Dict, data_class: Type) -> Any:
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
