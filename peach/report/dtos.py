import typing
from dataclasses import dataclass

from peach.misc.dtos import PaginationCriteriaDTO


@dataclass
class TaskListCriteria(PaginationCriteriaDTO):
    report_type: typing.Optional[str] = None
    user_id: typing.Optional[int] = None


@dataclass
class TaskExecutor:
    report_type: typing.Optional[str] = None
    executor: typing.Optional[str] = None
