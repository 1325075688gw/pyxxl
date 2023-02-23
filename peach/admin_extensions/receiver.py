from django.dispatch import receiver

from peach.admin.models import RolePermissionRel
from peach.admin.signals import post_add_rel

from .models import RolePermissionRelExtend


@receiver(post_add_rel)
def add_rel_handler(sender, instance: RolePermissionRel, limit_confs: dict, **kwargs):
    RolePermissionRelExtend.objects.update_or_create(
        rel=instance,
        defaults=dict(limit_confs=limit_confs),
    )
