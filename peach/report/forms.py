from marshmallow import fields

from peach.django.forms import PaginationSchema


class TaskListSchema(PaginationSchema):
    report_type = fields.String()
