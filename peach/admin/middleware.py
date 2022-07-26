import json
import logging

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from peach.admin.const import ACTION

from peach.admin.services import admin_service

from peach.django.header import (
    shorten_user_agent,
    get_client_ip,
    get_request_user_agent,
)

_LOGGER = logging.getLogger(__name__)


class OperationLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        pass

    def process_exception(self, request, exception):
        pass

    def process_response(self, request, response):
        try:
            if isinstance(response, (dict, HttpResponse)):
                handle_oper_record(request, response)
        except Exception as e:
            _LOGGER.info(f"OperationLogMiddleware  exception: {e}", exc_info=True)
        return response


def handle_oper_record(req, resp):
    if req.method not in ACTION or req.method == "GET":
        return
    if "/admin/login/" in req.path:  # 登录时不记录
        return
    try:
        resource_id = resp.get("id")
        action = ACTION[req.method]
        content = req.body.decode() if req.body else ""
        resource = req.permission_code if hasattr(req, "permission_code") else None
        if not resource:
            return
        if resource == "admin_user_add":  # 新增用户时，去除密码明文
            temp = json.loads(content)
            temp.pop("password")
            content = json.dumps(temp)
        user_agent = shorten_user_agent(get_request_user_agent(req))
        operator = req.user_id if hasattr(req, "user_id") else None
        ip = get_client_ip(req)
        admin_service.insert_record(
            resource, resource_id, action, content, operator, ip, user_agent
        )
    except Exception as e:
        _LOGGER.exception("insert record exception {}".format(e))
