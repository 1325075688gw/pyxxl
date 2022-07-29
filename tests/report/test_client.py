import json
from dataclasses import dataclass
from datetime import datetime
from enum import unique, IntEnum
from typing import Optional

from peach.misc.dtos import PaginationCriteriaDTO
from peach.report.client import _dict_to_dto


@dataclass
class RecordListCriteria(PaginationCriteriaDTO):
    resources: Optional[list] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    operator: Optional[str] = None
    action: Optional[int] = None
    ip: Optional[str] = None
    created_at_begin: Optional[datetime] = None
    created_at_end: Optional[datetime] = None


@unique
class AddCoinType(IntEnum):
    ACCOUNT = 1  # 账户
    SAFEBOX = 2  # 保险箱


@unique
class OperBlackType(IntEnum):
    ACCOUNT = 1  # 账号黑名单
    DEVICE = 2  # 设备黑名单
    WITHDRAW = 3  # 提现黑名单
    PAY = 4  # 支付黑名单
    TEST = 5  # 测试账号


@dataclass
class AddCoinFormCriteria(PaginationCriteriaDTO):
    user_id: Optional[int] = None
    type: Optional[AddCoinType] = None
    black_type: Optional[OperBlackType] = None
    created_at_start: Optional[datetime] = None
    created_at_end: Optional[datetime] = None


def test_dict_to_dto():
    data = """
    {"page_no": 1, "page_size": 30, "return_total": true, "export": true, "resources": [], "resource_id": null,
     "resource_name": null, "operator": null, "action": null, "ip": null, "created_at_begin": null,
     "created_at_end": null}
    """
    print("=============>1: ", data)
    ret = _dict_to_dto(json.loads(data), RecordListCriteria)
    print("\n", ret)

    data = """{"page_no": 1, "page_size": 30, "return_total": true, "export": true, "user_id": null, "type": null,
    "black_type": null, "created_at_start": null, "created_at_end": null}
    """

    print("=============>2: ", data)
    ret = _dict_to_dto(json.loads(data), AddCoinFormCriteria)
    print("\n", ret)
