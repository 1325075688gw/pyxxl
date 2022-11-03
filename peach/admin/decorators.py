from functools import wraps
import inspect

from django.conf import settings
from django.http import HttpRequest

from .exceptions import (
    ERROR_LIST_FUNC_MISS_ARGS,
    ERROR_USER_TOKEN_NOT_EXISTS,
    ERROR_VCODE_EMPTY,
    ERROR_VCODE_INCORRECT,
)
from .services import admin_service
from .safe_dog import safe_client
from . import auth
from peach.misc.exceptions import BizException


def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0]

        assert isinstance(request, HttpRequest)
        request = args[0]
        assert isinstance(request, HttpRequest)

        token = request.META.get(
            "HTTP_X_AUTH_TOKEN"
        )  # token被django转换成HTTP_TOKEN存放在META里面.

        if not token:
            raise BizException(ERROR_USER_TOKEN_NOT_EXISTS)

        user = admin_service.get_user_by_token(token, update=True)
        request.user_id = user["id"]
        request.token = token
        request.user = user
        return func(*args, **kwargs)

    return wrapper


def check_permission(permission_code):
    def decorator(func):
        def wrapper(*args, **kwargs):
            request = args[0]
            auth.check_permission(permission_code, request)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def list_func(func):
    """
    定义规范，查询列表方法必须有 page_size,page_no,order_by 参数
    :param func:
    :return:
    """
    func_args = inspect.getfullargspec(func).args
    need_args = ["page_size", "page_no", "order_by"]
    if not set(need_args).issubset(set(func_args)):
        raise BizException(ERROR_LIST_FUNC_MISS_ARGS)
    return func


def require_vcode(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0]
        assert isinstance(request, HttpRequest)

        user_id = int(request.META.get("HTTP_X_AUTH_USER"))
        check_user_vcode(request, user_id)

        return func(*args, **kwargs)

    return wrapper


def check_user_vcode(request, user_id):
    if not settings.DEBUG:
        vcode = request.META.get("HTTP_X_AUTH_VCODE")
        if not vcode:
            raise BizException(ERROR_VCODE_EMPTY)
        if not safe_client.verify_token(user_id, vcode, "127.0.0.1"):
            raise BizException(ERROR_VCODE_INCORRECT)
