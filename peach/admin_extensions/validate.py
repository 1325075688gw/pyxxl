# mypy: ignore-errors

import json
import logging
from json import JSONDecodeError

from peach.admin.models import Role
from peach.admin_extensions.models import RolePermissionRelExtend

_LOGGER = logging.getLogger(__name__)


def validate_permission_limit_by_role(obj: Role, permission_code: str) -> bool:
    try:
        rel = (
            obj.rolepermissionrel_set.select_related("rolepermissionrelextend")
            .filter(permission__code=permission_code)
            .first()
        )
        if not rel:
            return False
        limit_confs = rel.rolepermissionrelextend.limit_confs
        if not limit_confs:
            return False
        _limit_confs = json.loads(limit_confs)
        if not _limit_confs:
            return False
        return (
            True
            if list(filter(lambda x: x is not None, _limit_confs.values()))
            else False
        )
    except RolePermissionRelExtend.DoesNotExist as e:
        _LOGGER.warning(
            f"[AdminExtensions] RolePermissionRelExtend.DoesNotExist: {obj.name}, {permission_code}, {e}"
        )
        return False
    except JSONDecodeError as e:
        _LOGGER.warning(
            f"[AdminExtensions] JSONDecodeError: {obj.name}, {permission_code}, {e}"
        )
        return False
