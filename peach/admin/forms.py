from marshmallow import fields

from peach.django.forms import (
    BaseSchema,
    PaginationSchema,
    OptionField,
    StripStrField,
)
from .dto import UserListCriteria, RoleListCriteria, RecordListCriteria


class RegisterSchema(BaseSchema):
    name = StripStrField(required=True)
    password = fields.String(required=True)


class LoginSchema(BaseSchema):
    name = fields.String(required=True)
    password = fields.String(required=True)


class AddUserSchema(BaseSchema):
    name = fields.String(required=True)
    password = fields.String(required=True)
    enable = fields.Boolean(missing=False)
    role_ids = fields.List(fields.Integer())
    parent_id = fields.Integer()


class GetUserSchema(PaginationSchema):
    order_by = OptionField(
        [
            "last_login_at",
            "-last_login_at",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ],
        missing="-last_login_at",
    )
    name = fields.String()
    enable = fields.Boolean()
    role_id = fields.Integer()

    def make_criteria(self, data) -> UserListCriteria:
        return UserListCriteria(
            order_by=data.get("order_by"),
            name=data.get("name"),
            enable=data.get("enable"),
            role_id=data.get("role_id"),
        )


class UpdateUserSchema(BaseSchema):
    role_ids = fields.List(fields.Integer())
    enable = fields.Boolean(allow_none=True)


class UpdateUserPasswordSchema(BaseSchema):
    old_password = fields.String(required=True)
    new_password = fields.String(required=True)


class RolePermissionRelSchema(BaseSchema):
    permission_id = fields.Integer(required=True)
    include_fields = fields.List(fields.String(required=True))


class GetRoleSchema(PaginationSchema):
    name = fields.String()
    permission_code = fields.String()
    order_by = OptionField(
        [
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ],
        missing="-updated_at",
    )

    def make_criteria(self, data) -> RoleListCriteria:
        return RoleListCriteria(
            name=data.get("name"),
            permission_code=data.get("permission_code"),
            order_by=data.get("order_by"),
        )


class AddRoleSchema(BaseSchema):
    name = fields.String(required=True)
    desc = fields.String()
    permissions = fields.List(fields.Nested(RolePermissionRelSchema))


class UpdateRoleSchema(BaseSchema):
    name = fields.String(required=True)
    desc = fields.String()
    permissions = fields.List(fields.Nested(RolePermissionRelSchema))


class RecordListSchema(PaginationSchema):
    resources = fields.String(allow_none=True)
    resource_id = fields.String()
    resource_name = fields.String()
    operator = fields.String()
    action = fields.Integer()
    ip = fields.String()
    created_at_begin = fields.DateTime()
    created_at_end = fields.DateTime()
    order_by = fields.String(missing="-updated_at")

    def make_criteria(self, data, **kwargs) -> RecordListCriteria:
        return RecordListCriteria(
            resources=data["resources"].split(",") if data.get("resources") else [],
            resource_id=data.get("resource_id"),
            resource_name=data.get("resource_name"),
            operator=data.get("operator"),
            action=data.get("action"),
            ip=data.get("ip"),
            created_at_begin=data.get("created_at_begin"),
            created_at_end=data.get("created_at_end"),
            order_by=data.get("order_by"),
        )
