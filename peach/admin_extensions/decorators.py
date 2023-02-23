import typing
from functools import wraps

from peach.misc.util import dict_to_dto

from .dto import PermissionLimitDTO
from .models import RolePermissionRelExtend


def check_permission_limit_confs(limit_func: typing.Callable, limit_conf: typing.Type):
    """
    操作限制校验装饰器, validate_parameters 之后使用
    :param limit_func: 限制校验函数
    :param limit_conf: 限制配置
    :return:
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = args[0]

            if not request.user["is_super"]:
                # 这里用户可能关联多个角色，所以返回的是一个列表
                limit_confs = _get_user_permission_limit_confs(
                    request.user_id, request.permission_code
                )
                dto = PermissionLimitDTO(
                    user_id=request.user_id,
                    permission_code=request.permission_code,
                    limit_confs=[dict_to_dto(conf, limit_conf) for conf in limit_confs],
                    cleaned_data=request.cleaned_data,
                )
                limit_func(dto)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def _get_user_permission_limit_confs(
    user_id, permission_code
) -> typing.Union[list, None]:
    """
    返回某个用户对特定某个权限的操作限制配置
    :param user_id: 用户id
    :param permission_code: 权限code
    :return: [{'field1': 'value1', 'field2': 'value2'}, ...] or None
    """
    result = []
    rels = RolePermissionRelExtend.objects.filter(
        rel__role__user__id=user_id, rel__permission__code=permission_code
    )
    for each in rels:
        if each.limit_confs:
            result.append(each.limit_confs)
    return result
