from django.apps import AppConfig
from django.conf import settings
from peach.otel.conf import TraceConf
from peach.otel.trace import OtelTrace


class OtelConfig(AppConfig):
    name = "peach.otel"

    def ready(self):
        if hasattr(settings, "OTEL_TRACE_CONF"):
            OtelTrace(TraceConf(**settings.OTEL_TRACE_CONF)).startup()
