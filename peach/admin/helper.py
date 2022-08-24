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
