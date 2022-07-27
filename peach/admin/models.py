from django.db import models
from peach.django.models import BaseModel, ListField


class User(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    is_super = models.BooleanField(default=False)
    enable = models.BooleanField(default=True)
    roles = models.ManyToManyField("Role")
    deleted = models.BooleanField(default=False)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)
    login_count = models.IntegerField(default=0)  # 登陆次数
    last_login_at = models.DateTimeField(null=True)  # 最后登录时间


class Token(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, db_index=True)


class Role(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    desc = models.CharField(max_length=200, null=True)
    permissions = models.ManyToManyField("Permission", through="RolePermissionRel")
    can_update = models.BooleanField(default=True)

    def to_dict(self, fields=None, exclude=None, return_many_to_many=False):
        data = super().to_dict(fields, exclude, return_many_to_many)
        data["user_count"] = self.user_set.count()
        return data


class Permission(BaseModel):
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50, unique=True)
    sort_index = models.IntegerField(default=1)
    desc = models.CharField(max_length=200, null=True)
    full_path = models.CharField(max_length=100)
    is_leaf = models.BooleanField(default=False)
    fields = ListField(max_length=1000, null=True)

    class Meta:
        ordering = ["sort_index"]


class RolePermissionRel(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    include_fields = ListField(max_length=1000, null=True)

    class Meta:
        unique_together = ("role", "permission")


class Record(BaseModel):
    resource = models.CharField(max_length=100, null=True)
    resource_id = models.CharField(max_length=32, null=True)
    action = models.SmallIntegerField()
    content = models.TextField()
    operator = models.CharField(max_length=64, null=True)
    ip = models.CharField(max_length=100)
    user_agent = models.CharField(max_length=100)
