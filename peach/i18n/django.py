import logging
import threading

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .text import ResouceLoader

_LOGGER = logging.getLogger()

_LOCAL = threading.local()

_RES: ResouceLoader = None

_DEFAULT_LAN = "en"


def load_i18n_resource(path: str):
    global _RES
    _RES = ResouceLoader(path)


def set_local_lan(lan: str):
    _LOCAL.lan = lan


def clear_local_lan():
    if hasattr(_LOCAL, "lan"):
        del _LOCAL.lan


def get_local_lan() -> str:
    return getattr(_LOCAL, "lan", None)


def get_default_lan() -> str:
    """
    Local > settings.LANGUAGE_CODE > "en"
    """
    lan = get_local_lan()
    if lan:
        return lan

    return (
        settings.LANGUAGE_CODE if hasattr(settings, "LANGUAGE_CODE") else _DEFAULT_LAN
    )


def get_text(msg_id: str, lan: str = None, **kwargs):
    if not _RES:
        _LOGGER.warning("i18n resource has not been loaded")
        return msg_id

    return _RES.get_text(msg_id, lan or get_default_lan(), **kwargs)


class LocaleMiddleware(MiddlewareMixin):
    """
    Parse a request and decide what translation object to install in the
    current thread context. This allows pages to be dynamically translated to
    the language the user desires (if the language is available, of course).
    """

    _header_req_lan = "HTTP_ACCEPT_LANGUAGE"

    def process_request(self, request):
        clear_local_lan()
        lan = request.META.get(LocaleMiddleware._header_req_lan)
        if not _RES:
            _LOGGER.error(
                "django i18n plugin : load_i18n_resource must be executed before the service starts"
            )
            return
        if not lan:
            lan = settings.LANGUAGE_CODE
        if lan not in _RES.get_all_lans():
            lan = _DEFAULT_LAN
        set_local_lan(lan)
        request.LANGUAGE_CODE = lan

    def process_response(self, request, response):
        response.setdefault("Content-Language", get_default_lan())
        return response
