from typing import Optional
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
    resources: Optional[list] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    operator: Optional[str] = None
    action: Optional[int] = None
    ip: Optional[str] = None
    created_at_begin: Optional[datetime] = None
    created_at_end: Optional[datetime] = None
    order_by: Optional[str] = None
