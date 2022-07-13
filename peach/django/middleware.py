import logging
from datetime import datetime

from django.http import QueryDict, JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

from peach.django.views import PaginationResponse
from peach.misc.exceptions import BizException
from peach.django.json import JsonEncoder
from peach.misc.util import qdict_to_dict
from peach.misc.translation import set_local_language

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
        accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        if accept:
            set_local_language(accept.split(",")[0])
        else:
            set_local_language("zh-hans")

    def process_exception(self, request, exception):
        if isinstance(exception, BizException):
            _LOGGER.info(f"====> {exception.error_code}, {exception.detail_message}")
            response = dict(
                status=exception.error_code.code,
                msg=exception.detail_message,
                timestamp=datetime.now(),
            )
            if settings.DEBUG:
                _LOGGER.exception(
                    "catched error {} in {}, uid:{}".format(
                        exception.__class__.__name__,
                        request.path,
                        request.user_id if hasattr(request, "user_id") else None,
                    )
                )
            else:
                _LOGGER.warning(
                    "catched warning {} in {}, uid:{}".format(
                        exception.__class__.__name__,
                        request.path,
                        request.user_id if hasattr(request, "user_id") else None,
                    ),
                    exc_info=True,
                )

        else:
            response = dict(
                status=-1,
                msg="内部错误，请联系管理员",
                timestamp=datetime.now(),
            )
            _LOGGER.exception(
                "catched error {} in {}, uid:{}".format(
                    exception.__class__.__name__,
                    request.path,
                    request.user_id if hasattr(request, "user_id") else None,
                )
            )
        try:
            return JsonResponse(response, encoder=JsonEncoder, status=500)
        except Exception:
            _LOGGER.exception("cao")

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
        if isinstance(response, (dict, list, PaginationResponse)):
            wrap_data = dict(
                status=0,
                msg="OK",
                timestamp=datetime.now(),
            )
            if isinstance(response, PaginationResponse):
                response = dict(
                    total=response.total, items=response.items, **response.kwargs
                )
            wrap_data["data"] = response
            return JsonResponse(wrap_data, encoder=JsonEncoder)
        elif isinstance(response, str):
            return HttpResponse(response)
        elif response is None:
            return HttpResponse("")
        else:
            return response


class RPCMiddleware(ApiMiddleware):
    """远程接口， status返回200"""

    def process_exception(self, request, exception):

        if isinstance(exception, BizException):
            response = dict(
                status=exception.error_code.code,
                msg=exception.detail_message,
                timestamp=datetime.now(),
            )
            _LOGGER.warning(
                "biz error: %s ,path: %s, uid: %s",
                exception,
                request.path,
                request.user_id if hasattr(request, "user_id") else None,
            )
            return JsonResponse(response, encoder=JsonEncoder, status=400)
        else:
            response = dict(status=-1, msg="内部错误，请联系管理员", timestamp=timezone.now())
            logging.exception(
                "catched error %s in %s, uid:%s",
                exception.__class__.__name__,
                request.path,
                request.user_id if hasattr(request, "user_id") else None,
            )
            return JsonResponse(response, encoder=JsonEncoder, status=500)
