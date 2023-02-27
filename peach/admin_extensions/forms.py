from marshmallow import fields


class RolePermissionRelMixin:
    limit_confs = fields.Dict(allow_none=True)
