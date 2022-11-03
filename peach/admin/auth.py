from django.http import HttpRequest

from .exceptions import (
    ERROR_PERMISSION_NOT_AUTHORIZED,
)

from .services import admin_service
from peach.misc.exceptions import BizException


def check_permission(permission_code, request):
    request.permission_code = permission_code
    assert isinstance(request, HttpRequest)
    all_permission_codes = admin_service.get_user_all_permission_codes(request.user_id)
    perms = (
        set(permission_code) if isinstance(permission_code, list) else {permission_code}
    )
    if not perms.intersection(all_permission_codes):
        raise BizException(ERROR_PERMISSION_NOT_AUTHORIZED)
