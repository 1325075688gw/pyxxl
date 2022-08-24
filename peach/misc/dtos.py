from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Generic, TypeVar, List


@dataclass
class IdentityDTO:
    """
    包含`id`字段
    """

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return type(other) == type(self) and other.id == self.id


@dataclass
class MGIdentityDTO:
    """
    包含`id`字段
    """

    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return type(other) == type(self) and other.id == self.id


@dataclass
class PaginationCriteriaDTO:
    """
    分页查询器
    """

    page_no: int = 1
    page_size: int = 30
    return_total: bool = True
    export: bool = False


T = TypeVar("T")


@dataclass
class PaginationResultDTO(Generic[T]):
    """
    分页返回结果
    """

    total: int = 0
    data: List[T] = field(default_factory=list)
