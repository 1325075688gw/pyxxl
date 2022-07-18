import logging
from dataclasses import is_dataclass
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse, HttpResponse, QueryDict
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from peach.misc.util import qdict_to_dict
from peach.i18n.django import get_text
from peach.misc.exceptions import BizException
from peach.django.json import JsonEncoder

_LOGGER = logging.getLogger(__name__)


class ApiMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.incoming_ts = int(timezone.now().timestamp() * 1000)
        request.DATA = QueryDict("")
        if request.method == "GET":
            body = request.META["QUERY_STRING"]
        else:
            if not request.META.get("CONTENT_TYPE") or request.META.get(
                "CONTENT_TYPE"
            ).startswith("multipart/form-data"):
                return
            else:
                body = request.body.decode()
        request.DATA = qdict_to_dict(QueryDict(body))

    def process_exception(self, request, exception):
        print_msg = exception.__class__.__name__ + " : " + str(exception)
        user_id = request.user_id if hasattr(request, "user_id") else None
        if isinstance(exception, BizException):
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
