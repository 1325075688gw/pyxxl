import copy
import uuid
from fnmatch import fnmatch
from datetime import timedelta
from django.conf import settings

import bcrypt
from django.db import transaction
from django.db.models import F

from peach.report.api import report_decorator
from peach.i18n.django import get_text, exist_i18n_resource
from peach.misc import dt
from .. import signals
from ..const import ActionDesc, DEFAULT_PASSWORD

from ..exceptions import (
    ERROR_USER_NOT_EXISTS,
    ERROR_USER_PASSWORD_INCORRECT,
    ERROR_USER_PASSWORD_DIFFERENT,
    ERROR_USER_NAME_DUPLICATE,
    ERROR_USER_DISABLED,
    ERROR_ROLE_NAME_EXISTS,
    ERROR_ROLE_CAN_NOT_UPDATE,
    ERROR_ROLE_BIND_ONLY_LEAF_PERMISSION,
    ERROR_ROLE_NOT_ALLOW_SET_PERMISSION_ATTR,
    ERROR_ROLE_NOT_EXISTS,
    ERROR_PERMISSION_NOT_EXISTS,
    ERROR_USER_TOKEN_NOT_EXISTS,
    ERROR_USER_ROLES_NOT_EXISTS,
    ERROR_ROLE_CAN_NOT_DELETE,
    ERROR_ILLEGAL_PARAMS,
    ERROR_DISABLE_LOGIN_BY_TOKEN,
    ERROR_DISABLE_LOGIN_BY_PASSWORD,
)
from ..models import User, Role, RolePermissionRel, Permission, Record, Token
from ..dto import UserListCriteria, RoleListCriteria, RecordListCriteria
from peach.misc.dtos import PaginationResultDTO
from peach.django.models import paginate
from peach.misc.exceptions import BizException


def login_by_token(name, is_super):
    if getattr(settings, "LOGIN_BY_TOKEN_ENABLE", False) is False:
        raise BizException(ERROR_DISABLE_LOGIN_BY_TOKEN)

    user_info = get_or_create_user(name, is_super)

    token = create_token(user_info["id"])
    user_info.update(dict(token=token))
    return user_info


def get_or_create_user(name: str, is_super: bool) -> dict:
    user = User.objects.filter(name=name).first()
    if user is None:
        user_info = add_user(name, DEFAULT_PASSWORD, enable=True, is_super=is_super)
    elif user.enable and (not user.deleted):
        user_info = user.to_dict(
            exclude=["password", "deleted"], return_many_to_many=True
        )
    else:
        raise BizException(ERROR_USER_NAME_DUPLICATE)
    return user_info


def add_user(
    name, password, role_ids=None, parent_id=None, enable=None, is_super=False
):
    """
    ????????????
    """
    assert name
    assert password
    if role_ids:
        assert isinstance(role_ids, list)
    _check_password(password)
    _check_user_name_duplicate(name)
    parent = _get_user_by_id(parent_id) if parent_id else None

    encrypted_pwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    with transaction.atomic():
        user = User.objects.create(
            name=name,
            password=encrypted_pwd,
            parent=parent,
            enable=enable,
            is_super=is_super,
        )
        _bind_user_to_groups(user, role_ids)
        signals.post_add_user.send(sender=User, instance=user)

    return user.to_dict(exclude=["password", "deleted"])


def _bind_user_to_groups(user, role_ids):
    if not role_ids:
        return
    for role_id in role_ids:
        role = _get_role(role_id)
        user.roles.add(role)


def delete_user(user_id):
    """
    ????????????
    """
    assert isinstance(user_id, int)
    with transaction.atomic():
        user = _get_user_by_id(user_id, check_enable=False)
        user.deleted = True
        user.enable = False
        user.save()
        user.roles.clear()
        signals.post_del_user.send(sender=User, instance=user)


def update_user(user_id, role_ids=None, enable=None):
    """
    ?????????????????????????????????????????????
    """
    if role_ids:
        assert isinstance(role_ids, list)
    with transaction.atomic():
        user = _get_user_by_id(user_id, check_enable=False)
        user.roles.clear()
        if enable is not None:
            user.enable = enable
        user.save()
        _bind_user_to_groups(user, role_ids)
        signals.post_update_user.send(sender=User, instance=user)


def update_user_login_count(user_id):
    User.objects.filter(pk=user_id).update(login_count=F("login_count") + 1)


def update_user_last_login_time(user_id):
    User.objects.filter(pk=user_id).update(last_login_at=dt.local_now())


def get_user_by_id(user_id, check_enable=True, with_roles=False, check_deleted=True):
    user = _get_user_by_id(
        user_id, check_enable=check_enable, check_deleted=check_deleted
    )
    result = user.to_dict(exclude=["password"])
    if with_roles:
        result["roles"] = [e.to_dict(fields=["id", "name"]) for e in user.roles.all()]
    return result


def list_users(criteria: UserListCriteria):
    query = User.objects.filter(deleted=False)
    if criteria.name:
        query = query.filter(name=criteria.name)
    if criteria.enable is not None:
        query = query.filter(enable=criteria.enable)
    if criteria.role_id:
        query = query.filter(roles__exact=criteria.role_id)
    if criteria.order_by:
        query = query.order_by(criteria.order_by)
    return PaginationResultDTO(
        query.count(),
        [
            e.to_dict(exclude=["password", "deleted"], return_many_to_many=True)
            for e in paginate(query, criteria.page_no, criteria.page_size)
        ],
    )


def disable_user(user_id):
    """
    ????????????
    """
    user = _get_user_by_id(user_id)
    user.enable = False
    user.save()


def enable_user(user_id):
    """
    ????????????
    """
    user = _get_user_by_id(user_id, check_enable=False)
    user.enable = True
    user.save()


def verify_password(name, password):
    """
    ?????????????????????
    """
    user = _get_user_by_name(name)
    if not user:
        raise BizException(ERROR_USER_NOT_EXISTS)
    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        raise BizException(ERROR_USER_PASSWORD_INCORRECT)
    return user.to_dict(exclude=["password", "deleted"], return_many_to_many=True)


def create_token(user_id):
    new_token = str(uuid.uuid4())
    Token.objects.create(user_id=user_id, token=new_token)
    return new_token


def get_user_by_token(token, update=False):
    if settings.DEBUG:
        valid_created_at = dt.local_now() - timedelta(days=14)
    else:
        valid_created_at = dt.local_now() - timedelta(hours=6)
    token = Token.objects.filter(
        token=token,
        updated_at__gt=valid_created_at,
        user__enable=True,
    ).first()
    if not token:
        raise BizException(ERROR_USER_TOKEN_NOT_EXISTS)
    if update:
        token.save()
    return token.user.to_dict(exclude=["password"], return_many_to_many=True)


def delete_token(user_id, token):
    Token.objects.filter(user_id=user_id, token=token).delete()


def login(name, password):
    if getattr(settings, "LOGIN_BY_PASSWORD_ENABLE", True) is False:
        raise BizException(ERROR_DISABLE_LOGIN_BY_PASSWORD)

    user = verify_password(name, password)
    if not user["is_super"] and not user["roles"]:
        raise BizException(ERROR_USER_ROLES_NOT_EXISTS)

    token = create_token(user["id"])
    user.update(dict(token=token))
    return user


def logout(user_id, token):
    Token.objects.filter(user_id=user_id, token=token).delete()


def reset_password_after_verify_old_success(user_id, old_password, new_password):
    """
    ????????????, ?????????????????????
    """
    user = _get_user_by_id(user_id)
    if not bcrypt.checkpw(old_password.encode("utf-8"), user.password.encode("utf-8")):
        raise BizException(ERROR_USER_PASSWORD_INCORRECT)
    reset_password(user_id, new_password)


def reset_password(user_id, password):
    """
    ????????????
    """
    _check_password(password)
    user = _get_user_by_id(user_id)
    if bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        raise BizException(ERROR_USER_PASSWORD_DIFFERENT)
    encrypted_pwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    user.password = encrypted_pwd
    user.save()
    Token.objects.filter(user_id=user_id).delete()


def get_role_id_by_id(user_id):
    user = _get_user_by_id(user_id)
    role = user.roles.first()
    return role.id


def get_user_name_group_by_id(user_id, include_self=True, include_children=False):
    user = _get_user_by_id(user_id)
    user_name_list = [user.name] if include_self else []
    if include_children:
        children = User.objects.filter(parent=user).all()
        for child in children:
            user_name_list.append(child.name)
    return user_name_list


def _get_user_by_id(user_id, check_deleted=True, check_enable=True):
    user = User.objects.filter(pk=user_id).first()
    _check_user_valid(user, check_deleted, check_enable)
    return user


def _get_user_by_name(name, check_deleted=True, check_enable=True):
    user = User.objects.filter(name=name).first()
    _check_user_valid(user, check_deleted, check_enable)
    return user


def _check_user_name_duplicate(name):
    if User.objects.filter(name=name).exists():
        raise BizException(ERROR_USER_NAME_DUPLICATE)


def _check_user_valid(user, check_deleted, check_enable):
    if not user:
        raise BizException(ERROR_USER_NOT_EXISTS)
    if check_deleted and user.deleted:
        raise BizException(ERROR_USER_NOT_EXISTS)
    if check_enable and not user.enable:
        raise BizException(ERROR_USER_DISABLED)


def _check_password(password):
    errors = []
    if not any(x.isupper() for x in password):
        errors.append("????????????????????????\n")
    if not any(x.islower() for x in password):
        errors.append("????????????????????????\n")
    if not any(x.isdigit() for x in password):
        errors.append("??????????????????\n")
    if not len(password) >= 6:
        errors.append("????????????????????????6\n")
    if errors:
        raise BizException(ERROR_ILLEGAL_PARAMS, "???????????????" + "".join(errors))


##################################################
##################################################


def add_role(name, desc=None, permissions=None):
    """
    ??????????????????????????????
    """
    _check_role_permission_rel(permissions)
    _check_role_name_duplicate(name)

    with transaction.atomic():
        role = Role.objects.create(name=name, desc=desc)
        _bind_role_and_permissions(role, permissions)

    return role.to_dict()


def _check_role_name_duplicate(name):
    if Role.objects.filter(name=name).exists():
        raise BizException(ERROR_ROLE_NAME_EXISTS)


def delete_role(role_id):
    """
    ??????????????????????????????????????????????????????
    """
    role = _get_role(role_id)
    if role.user_set.exists():
        raise BizException(ERROR_ROLE_CAN_NOT_DELETE)
    deleted_count, _ = role.delete()
    return deleted_count > 0


def update_role(role_id, name, desc=None, permissions=None):
    """
    ???????????????????????????????????????
    """
    _check_role_permission_rel(permissions)
    role = _get_role(role_id)
    if not role.can_update:
        raise BizException(ERROR_ROLE_CAN_NOT_UPDATE)
    with transaction.atomic():
        role.name = name
        role.desc = desc
        role.save()
        # ???????????????????????????????????????????????????????????????????????????
        # ??????????????????????????????????????????????????????????????????????????????
        role.permissions.clear()
        _bind_role_and_permissions(role, permissions)


def get_role(role_id, with_permissions=False):
    """
    ??????????????????, ?????? with_permissions ???True????????????????????????????????????
    :return {'permission': list<RolePermissionBO>}
    """

    def _wrapper_rel_extend(e):
        res = e.to_dict(fields=["permission", "include_fields"])
        if hasattr(
            e, "rolepermissionrelextend"
        ):  # ?????? peach.admin_extensions ??????, ??????????????????
            res["limit_confs"] = e.rolepermissionrelextend.limit_confs or None
        return res

    role = _get_role(role_id)
    result = role.to_dict()
    if with_permissions:
        permissions = RolePermissionRel.objects.filter(role=role)
        result["permissions"] = [_wrapper_rel_extend(e) for e in permissions]
    return result


def list_roles(criteria: RoleListCriteria):
    query = Role.objects.all().order_by(criteria.order_by)
    if criteria.name:
        query = query.filter(name=criteria.name)
    if criteria.permission_code:
        query = query.filter(
            permissions__code__in=get_leaf_permissions([criteria.permission_code])
        ).distinct()
    return PaginationResultDTO(
        query.count(),
        [e.to_dict() for e in paginate(query, criteria.page_no, criteria.page_size)],
    )


def get_all_roles():
    query = Role.objects.all()
    return [{"role_id": e.id, "role_name": e.name} for e in query]


def _bind_role_and_permissions(role, permissions):
    if not permissions:
        return
    for each in permissions:
        permission_id = each.get("permission_id")
        include_fields = each.get("include_fields")
        limit_confs = each.get("limit_confs")
        permission = _get_permission(permission_id)
        if not permission.is_leaf:
            raise BizException(ERROR_ROLE_BIND_ONLY_LEAF_PERMISSION, permission_id)
        if not permission.fields and include_fields:
            raise BizException(ERROR_ROLE_NOT_ALLOW_SET_PERMISSION_ATTR, permission_id)
        rel = RolePermissionRel.objects.create(
            role=role,
            permission=permission,
            include_fields=include_fields,
        )
        signals.post_add_rel.send(
            sender=RolePermissionRel, instance=rel, limit_confs=limit_confs
        )


def _check_role_permission_rel(permissions):
    if permissions:
        assert isinstance(permissions, list)


def _get_role(role_id):
    role = Role.objects.filter(pk=role_id).first()
    if not role:
        raise BizException(ERROR_ROLE_NOT_EXISTS, role_id)
    return role


##################################################
##################################################


def get_user_permission_include_fields(user_id, permission_code):
    """
    ????????????????????????????????????????????????????????????
    :param user_id:
    :param permission_code:
    :return: {field1, field2, ...}
    """
    user = _get_user_by_id(user_id)
    result = set()
    if user.is_super:
        permission = Permission.objects.get(code=permission_code)
        if permission.fields:
            result = set(permission.fields)
    else:
        rels = RolePermissionRel.objects.filter(
            role__user__id=user_id, permission__code=permission_code
        )
        for each in rels:
            if each.include_fields:
                result.update(set(each.include_fields))
    return result


def get_user_all_permission_codes(user_id):
    """
    ????????????????????????
    ???????????????????????? 1/2/3/ ????????????????????????????????????1???2???3?????????????????????????????????
    ???????????????????????????????????????????????????????????????

    :param user_id:
    :return: {permission_code, ...}
    """
    result = set()
    user = _get_user_by_id(user_id)
    if user.is_super:
        result = {e.code for e in Permission.objects.all()}
    else:
        roles = user.roles.all()
        for role in roles:
            permissions = role.permissions.all()
            for permission in permissions:
                for each in _get_ancestor_include_current_permission(permission):
                    result.add(each["code"])

    return result


def get_total_permission_tree():
    """
    ?????????????????????????????????
    """
    result = []
    index_map = copy.deepcopy(get_permission_index_map_cache())

    need_translate = exist_i18n_resource()

    for pk, each in index_map.items():
        if need_translate:
            each["name"] = get_text(msg_id=each["code"])

        if each["parent_id"]:
            parent = index_map[each["parent_id"]]
            if "children" in parent:
                parent["children"].append(index_map[pk])
            else:
                parent["children"] = [index_map[pk]]
        else:
            result.append(index_map[pk])
    return result


def get_resource_map():
    name_code_map = (
        Permission.objects.filter(is_leaf=True)
        .values_list("parent__name", "parent__code")
        .order_by("parent__name")
    )
    return dict(name_code_map)


ALL_PERMISSION_CACHE = None


def get_permission_index_map_cache():
    global ALL_PERMISSION_CACHE
    if ALL_PERMISSION_CACHE:
        return ALL_PERMISSION_CACHE
    all_permissions = list(Permission.objects.all())
    ALL_PERMISSION_CACHE = {
        e.pk: e.to_dict(
            fields=["id", "parent", "name", "code", "fields", "is_leaf", "full_path"]
        )
        for e in all_permissions
    }
    return ALL_PERMISSION_CACHE


def get_permission_by_code(code):
    assert code
    permission = Permission.objects.filter(code=code).first()
    if not permission:
        raise BizException(ERROR_PERMISSION_NOT_EXISTS, code)
    return permission.to_dict()


def get_permission_parent_name_map():
    permission = Permission.objects.values_list("code", "parent__name")
    return dict(permission)


def _get_permission(permission_id):
    permission = Permission.objects.filter(pk=permission_id).first()
    if not permission:
        raise BizException(ERROR_PERMISSION_NOT_EXISTS, permission_id)
    return permission


def _get_ancestor_include_current_permission(permission):
    ancestor_ids = [int(e) for e in permission.full_path.split("/") if e]
    return [get_permission_index_map_cache()[e] for e in ancestor_ids]


def get_leaf_permissions(codes):
    permission_mapper = get_permission_index_map_cache()
    permission_mapper = {p["code"]: p for p in permission_mapper.values()}
    _codes = list()
    for code in codes:
        if "*" in code:
            for _code in permission_mapper:
                if fnmatch(_code, code):
                    _codes.append(_code)
        else:
            _codes.append(code)
    _codes = set(_codes)
    permissions = list()
    for _code in _codes:
        if _code in permission_mapper:
            permission = permission_mapper[_code]
            if permission["is_leaf"]:
                permissions.append(_code)
            else:
                if permission["parent_id"]:
                    _permissions = [
                        p["code"]
                        for p in permission_mapper.values()
                        if f"/{permission['id']}/" in p["full_path"] and p["is_leaf"]
                    ]
                else:
                    _permissions = [
                        p["code"]
                        for p in permission_mapper.values()
                        if p["full_path"].startswith(f"{permission['id']}/")
                        and p["is_leaf"]
                    ]
                permissions += _permissions
    return list(set(permissions))


def insert_record(resource, resource_id, action, content, operator, ip, user_agent):
    record = Record.objects.create(
        resource=resource,
        resource_id=resource_id,
        action=action,
        content=content,
        operator=operator,
        ip=ip,
        user_agent=user_agent,
    )
    return record.to_dict()


def get_record_list(criteria: RecordListCriteria):
    query = Record.objects.all()
    if criteria.operator:
        query = query.filter(operator=criteria.operator)
    if criteria.resources:
        query = query.filter(resource__in=get_leaf_permissions(criteria.resources))
    if criteria.resource_id:
        query = query.filter(resource_id=criteria.resource_id)
    if criteria.action:
        query = query.filter(action=criteria.action)
    if criteria.ip:
        query = query.filter(ip=criteria.ip)
    if criteria.created_at_begin:
        query = query.filter(created_at__gte=criteria.created_at_begin)
    if criteria.created_at_end:
        query = query.filter(created_at__lte=criteria.created_at_end)
    if criteria.resource_name:
        permissions = Permission.objects.filter(parent__name=criteria.resource_name)
        codes = {permission.code for permission in permissions}
        query = query.filter(resource__in=codes)
    return (
        query.count(),
        [
            e.to_dict()
            for e in paginate(
                query.order_by(criteria.order_by), criteria.page_no, criteria.page_size
            )
        ],
    )


@report_decorator(RecordListCriteria)
def export_record(criteria: RecordListCriteria):
    cn_header = ["????????????", "?????????", "????????????", "??????ID", "????????????", "????????????", "ip??????", "??????"]
    _, items = get_record_list(criteria)
    data = []
    permission_parent_name_map = get_permission_parent_name_map()
    user_map = dict(User.objects.values_list("id", "name"))
    for item in items:
        data.append(
            [
                dt.utc_to_local_str(item.get("created_at")),
                user_map.get(item.get("operator"), ""),
                permission_parent_name_map.get(item.get("resource"), ""),
                item.get("resource_id"),
                item.get("content"),
                ActionDesc.get(item.get("action")),
                item.get("ip"),
                item.get("user_agent"),
            ]
        )
    return len(data), cn_header, data
