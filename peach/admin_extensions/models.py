# mypy: ignore-errors
from django.db import models

from peach.admin.models import RolePermissionRel
from peach.django.models import DictField, BaseModel


class RolePermissionRelExtend(BaseModel):
    rel = models.OneToOneField(RolePermissionRel, on_delete=models.CASCADE)
    limit_confs = DictField(max_length=1000, null=True)
