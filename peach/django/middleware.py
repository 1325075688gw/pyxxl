import json
import logging
from dataclasses import is_dataclass
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse, HttpResponse, QueryDict
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from peach.admin.const import ACTION
from peach.django.header import (
    get_client_ip,
    shorten_user_agent,
    get_request_user_agent,
)
from peach.misc.util import qdict_to_dict
from peach.i18n.django import get_text
from peach.misc.exceptions import BizException, IllegalRequestException
from peach.django.json import JsonEncoder

_LOGGER = logging.getLogger(__name__)


class ApiMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.incoming_ts = int(timezone.now().timestamp() * 1000)
        request.DATA = QueryDict("")
        if request.method == "GET":
            body = request.META["QUERY_STRING"]
        else:
            if (
                not request.META.get("CONTENT_TYPE")
                or request.META.get("CONTENT_TYPE").startswith("multipart/form-data")
                or request.path == "/api/upload_file/"
            ):
                body = None
            else:
                body = request.body.decode()
        request.DATA = qdict_to_dict(QueryDict(body))

    def process_exception(self, request, exception):
        print_msg = exception.__class__.__name__ + " : " + str(exception)
        user_id = request.user_id if hasattr(request, "user_id") else None
        if isinstance(exception, IllegalRequestException):
            if settings.DEBUG:
                _LOGGER.exception(
                    f"IllegalRequestException: {print_msg}, path: {request.path}, uid: {user_id}"
                )
            else:
                _LOGGER.warning(
                    f"IllegalRequestException: {print_msg}, path: {request.path}, uid: {user_id}"
                )
            return HttpResponse(str(exception), status=400)
        elif isinstance(exception, BizException):
            msg = get_text(f"err_{exception.error_code.code}")
            response = dict(
                status=exception.error_code.code,
                msg=msg,
                timestamp=datetime.now(),
            )
            if settings.DEBUG:
                _LOGGER.exception(
                    f"BizException: {print_msg}, path: {request.path}, uid: {user_id}"
                )
            else:
                _LOGGER.warning(
                    f"BizException: {print_msg}, path: {request.path}, uid: {user_id}"
                )
            return JsonResponse(response, encoder=JsonEncoder, status=400)
        else:
            response = dict(status=-1, msg="内部错误，请联系管理员", timestamp=timezone.now())
            _LOGGER.exception(
                f"Exception: {print_msg}, path: {request.path}, uid: {user_id}"
            )
            return JsonResponse(response, encoder=JsonEncoder, status=500)

    def process_response(self, request, response):
        request.finish_ts = int(timezone.now().timestamp() * 1000)

        delta_t3_t2 = request.finish_ts - request.incoming_ts  # 程序处理时间 t3-t2
        user_id = request.user_id if hasattr(request, "user_id") else None
        _LOGGER.info(
            "URL: {method}: {api_url}, Duration: ∆32:{t3_t2}, user_id:{user_id}, params:{params}".format(
                method=request.method.upper(),
                api_url=request.path,
                t3_t2=delta_t3_t2,
                user_id=user_id,
                params=request.DATA if "/admin/login/" not in request.path else None,
            )
        )

        if isinstance(response, (dict, list)) or is_dataclass(response):
            wrap_data = dict(status=0, msg="OK", timestamp=timezone.now())
            wrap_data["data"] = response
            return JsonResponse(wrap_data, encoder=JsonEncoder)
        elif isinstance(response, str):
            return HttpResponse(response)
        elif response is None:
            return HttpResponse("")
        else:
            return response


class OperationLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        pass

    def process_exception(self, request, exception):
        pass

    def process_response(self, request, response):
        try:
            if isinstance(response, (dict, HttpResponse)):
                handle_oper_record(request, response)
        except Exception:
            _LOGGER.info("OperationLogMiddleware  exception", exc_info=True)
        return response


def handle_oper_record(req, resp):
    if req.method not in ACTION:
        return

    # 新增导出事件记录
    if req.method == "GET":
        if not req.GET.get("export"):
            return
        # 导出没有数据的记录, resource_id 设置为 0
        resp["id"] = 0

    try:
        resource_id = resp.get("id", 0)
        action = ACTION[req.method]
        content_type = req.META.get("CONTENT_TYPE")
        content = req.body.decode() if req.body else ""

        temp = dict()
        if content_type is not None and content_type.startswith("application/json"):
            temp = json.loads(content) if content else dict()
        elif content_type == "application/x-www-form-urlencoded":
            temp = QueryDict(content).copy()
        resource = req.permission_code if hasattr(req, "permission_code") else None
        operator = req.user_id if hasattr(req, "user_id") else None
        ip = get_client_ip(req)
        user_agent = shorten_user_agent(get_request_user_agent(req))
        if "/admin/login/" in req.path:  # 登录时去除密码明文
            resource = "admin_login"
            operator = resp["id"]
            temp.pop("password")

        from peach.admin.services import admin_service

        if not resource:
            return
        if resource == "admin_user_add":
            temp.pop("password")
        if isinstance(resource, list):
            resource = resource[0]
        admin_service.insert_record(
            resource,
            resource_id,
            action,
            json.dumps(temp),
            operator,
            ip,
            user_agent,
        )
    except Exception as e:
        _LOGGER.exception("insert record exception {}".format(e))
