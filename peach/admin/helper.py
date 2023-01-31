from django.conf import settings

from .services import admin_service


def wrapper_record_info(record_items):
    resp_items = []
    for record_item in record_items:
        record = admin_service.get_user_by_id(
            record_item["operator"], check_enable=False, check_deleted=False
        )
        record_item["operator_name"] = record["name"]
        permission = admin_service.get_permission_by_code(record_item["resource"])
        record_item["resource_name"] = permission["name"]
        resp_items.append(record_item)
    return resp_items


def wrapper_language_code(user_info: dict):
    user_info["lang"] = settings.LANGUAGE_CODE
    return user_info


def wrapper_include_fields(include_fields: list, data: list):
    if not data or not include_fields:
        return []

    return [_filter_fields(include_fields, item) for item in data]


def _filter_fields(include_fields: list, item: dict):
    _item = dict()
    for key in item.keys():
        if key not in include_fields:
            continue
        _item[key] = item[key]
    return _item
