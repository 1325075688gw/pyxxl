from dataclasses import dataclass
from datetime import datetime

from peach.misc.dtos import PaginationCriteriaDTO


@dataclass
class UserListCriteria(PaginationCriteriaDTO):
    order_by: str = None
    name: str = None
    enable: int = None
    role_id: int = None


@dataclass
class RoleListCriteria(PaginationCriteriaDTO):
    name: str = None
    permission_code: str = None


@dataclass
class RecordListCriteria(PaginationCriteriaDTO):
    resources: list = None
    resource_id: str = None
    resource_name: str = None
    operator: str = None
    action: int = None
    ip: str = None
    created_at_begin: datetime = None
    created_at_end: datetime = None
