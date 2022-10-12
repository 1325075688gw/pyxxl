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
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

_LOGGER = logging.getLogger(__name__)


class OtelTrace:
    def __init__(self, conf: TraceConf):
        self.conf = conf

    def instrument(self):
        _LOGGER.info("startup otel trace instrument...")

        self._django_instrument()
        self._db_instrument()
        if self.conf.enable_grpc_client:
            self._grpc_client_instrument()
        if self.conf.enable_grpc_server:
            self._grpc_server_instrument()

    def init_trace_provider(self):
        """初始化 trace"""
        _LOGGER.info("init otel trace provider...")
        resource = Resource(attributes={SERVICE_NAME: self.conf.service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        if not self.conf.debug:
            endpoint = f"{self.conf.endpoint_host}:{self.conf.endpoint_port}"
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(
                        endpoint=endpoint,
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

    def _db_instrument(self):
        """启用 db 自动检测"""
        PymongoInstrumentor().instrument()  # MongoDB trace
        # PyMySQLInstrumentor().instrument()  # MySQL trace(有报错，暂时无法使用，需要研究一下)
        # RedisInstrumentor().instrument()  # Redis trace(感觉意义不大，暂不启用)
