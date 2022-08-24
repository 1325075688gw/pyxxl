from marshmallow import fields

from peach.django.forms import PaginationSchema

from .dtos import TaskListCriteria


class TaskListSchema(PaginationSchema):
    report_type = fields.String()

    def make_criteria(self, data) -> TaskListCriteria:
        return TaskListCriteria(
            report_type=data.get("report_type"),
        )
