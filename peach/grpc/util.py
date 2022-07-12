import decimal
import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, date, time
from enum import Enum
from functools import wraps
from typing import Type, Any, Union
import typing

from dacite import from_dict, Config
from django.conf import settings
from google.protobuf.json_format import MessageToDict, Parse
from google.protobuf.message import Message

from django import db
from peach.log import trace_logging

from peach.misc import dt
from peach.misc.exceptions import BizException, IllegalRequestException

_LOGGER = logging.getLogger(__name__)


def read_credential_file(path):
    with open(path, "rb") as f:
        return f.read()


def msg_to_dto(msg: Message, data_class: Type) -> Any:
    data = MessageToDict(
        msg, use_integers_for_enums=True, preserving_proto_field_name=True
    )
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


def data_to_message(data: Union[Any, dict], msg_class: Type[Message]) -> Message:
    return Parse(
        json.dumps(data, cls=JsonEncoder), msg_class(), ignore_unknown_fields=True
    )


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return int(o.timestamp() * 1000)
        elif isinstance(o, date):
            return o.strftime("%Y-%m-%d")
        elif isinstance(o, time):
            return o.strftime("%H:%M:%S")
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, Enum):
            return str(o.value)
        elif is_dataclass(o):
            return asdict(o)
        else:
            return super().default(o)


def wrap_response(resp: Message):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if settings.DEBUG:
                _LOGGER.debug(f"[invoke rpc req]{func.__name__}, params: {args[1]}")
            _resp = resp() if isinstance(resp, type) else resp
            try:
                trace_logging.clear_trace()
                db.close_old_connections()
                result = func(*args, **kwargs)
            except BizException as ex:
                _resp.header.status = ex.error_code.code
                _resp.header.msg = ex.error_code.message or ""
                _LOGGER.debug(f"[invoke rpc BizException]: {func.__name__}, {ex}")
                return _resp
            except Exception:
                _LOGGER.exception(f"[invoke rpc error]: {func.__name__}")
                raise
            if result:
                Parse(
                    json.dumps(result, cls=JsonEncoder),
                    _resp,
                    ignore_unknown_fields=True,
                )
            if settings.DEBUG:
                _LOGGER.debug(f"[invoke rpc resp]{func.__name__}, resp: {_resp}")

            return _resp

        return wrapper

    return decorator


def validate_response(msg, known_biz_errs: typing.List[int] = None):
    code = msg.header.status
    if code != 0:
        if known_biz_errs and code in known_biz_errs:
            return
        else:
            # raise IllegalRequestException(f"code: {code} - msg: {msg.header.msg}")
            raise BizException(msg.header.status, msg.header.msg)
