from marshmallow import fields

from peach.django.forms import BaseSchema


class S3Schema(BaseSchema):
    path = fields.String(required=True)
