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
from .helper import wrapper_include_fields
from .services import admin_service, sso_service
from .safe_dog import safe_client
from . import auth
from peach.misc.exceptions import BizException
from peach.django.views import PaginationResponse


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


def check_permission(permission_code, check_include_fields=False):
    """
    权限校验装饰器
    :param permission_code: 权限code
    :param check_include_fields: 是否校验过滤返回结果中的字段是否在权限中
    :return:
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            request = args[0]
            request.permission_code = permission_code
            auth.check_permission(permission_code, request)

            request.include_fields = None
            if check_include_fields:
                request.include_fields = list(
                    admin_service.get_user_permission_include_fields(
                        request.user_id, permission_code
                    )
                )

            response = func(*args, **kwargs)

            if check_include_fields:
                # 响应过滤处理
                # 目前只针对 response 为 dict(total=0,items=[]) 和 PaginationResponse(total=0,items=[]) 类型的数据进行过滤
                if isinstance(response, PaginationResponse):
                    items = wrapper_include_fields(
                        request.include_fields, response.items
                    )
                    response = PaginationResponse(
                        items=items, total=response.total if items else 0
                    )
                elif isinstance(response, dict) and isinstance(
                    response.get("items"), list
                ):
                    items = wrapper_include_fields(
                        request.include_fields, response["items"]
                    )
                    response = dict(
                        items=items,
                        total=response["total"]
                        if items and response.get("total")
                        else 0,
                    )

            return response

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


def check_user_vcode(request, user_id, username: str = None):
    if not settings.DEBUG:
        vcode = request.META.get("HTTP_X_AUTH_VCODE")
        if not vcode:
            raise BizException(ERROR_VCODE_EMPTY)

        if getattr(settings, "SSO_VERIFY_VCODE_ENABLE", False):
            username = username or request.user["name"]
            if not sso_service.verify_vcode(username, vcode):
                raise BizException(ERROR_VCODE_INCORRECT)
        elif getattr(settings, "SAFE_DOG_ENABLE", True):
            if not safe_client.verify_token(user_id, vcode, "127.0.0.1"):
                raise BizException(ERROR_VCODE_INCORRECT)
