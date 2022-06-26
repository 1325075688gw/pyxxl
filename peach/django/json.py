import decimal
import json
from dataclasses import is_dataclass, asdict
from datetime import datetime, date, time
from enum import Enum

from django.utils import timezone


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.astimezone(timezone.get_current_timezone()).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
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
