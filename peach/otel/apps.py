import logging
import threading

from django.apps import AppConfig
from django.conf import settings
from peach.otel.conf import TraceConf
from peach.otel.trace import OtelTrace

_LOGGER = logging.getLogger(__name__)


class OtelConfig(AppConfig):
    name = "peach.otel"

    def ready(self):
        if not hasattr(settings, "OTEL_TRACE_CONF") or not settings.OTEL_TRACE_CONF.get(
            "enable"
        ):
            return

        if settings.OTEL_TRACE_CONF.get("endpoint_host") is None:
            _LOGGER.warning("otel endpoint_host is not configured")
            return

        otel_trace = OtelTrace(TraceConf(**settings.OTEL_TRACE_CONF))

        def _init_trace_provider() -> None:
            # 等待应用完全初始化之后再初始化 otel trace provider, 以解决线上启动报错问题
            self.apps.ready_event.wait()
            otel_trace.init_trace_provider()

        threading.Thread(target=_init_trace_provider).start()
        otel_trace.instrument()
