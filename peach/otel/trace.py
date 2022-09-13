import logging

from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.grpc import (
    GrpcInstrumentorClient,
    GrpcInstrumentorServer,
)
from peach.otel.conf import TraceConf
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

_LOGGER = logging.getLogger(__name__)


class OtelTrace:
    def __init__(self, conf: TraceConf):
        self.conf = conf

    def startup(self):
        if not self.conf.enable:
            return

        _LOGGER.info("startup otel trace...")

        self._init_trace()
        self._django_instrument()
        if self.conf.enable_grpc_client:
            self._grpc_client_instrument()
        if self.conf.enable_grpc_server:
            self._grpc_server_instrument()

    def _init_trace(self):
        """初始化 trace"""
        resource = Resource(attributes={SERVICE_NAME: self.conf.service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        if not self.conf.debug:
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(
                        endpoint=self.conf.endpoint,
                        insecure=True,
                    )
                )
            )
        else:
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )

    def _django_instrument(self):
        """启用 django 自动检测"""
        DjangoInstrumentor().instrument()

    def _grpc_client_instrument(self):
        """启用 grpc 客户端自动检测"""
        GrpcInstrumentorClient().instrument()

    def _grpc_server_instrument(self):
        """启用 grpc 服务端自动检测"""
        GrpcInstrumentorServer().instrument()
