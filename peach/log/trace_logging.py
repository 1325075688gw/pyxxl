import logging
import threading
import uuid

from peach.otel import trace_helper

_LOG_THREAD_VALUE = threading.local()


def clear_trace():
    try:
        del _LOG_THREAD_VALUE.trace_id
    except AttributeError:
        pass


def get_trace_id() -> str:
    # 串联 OTel trace id
    otel_trace_id = trace_helper.get_trace_context().trace_id
    if otel_trace_id:
        return hex(otel_trace_id)[2:]  # 转16进制，去掉0x

    try:
        return _LOG_THREAD_VALUE.trace_id
    except AttributeError:
        _LOG_THREAD_VALUE.trace_id = trace_id = uuid.uuid4().hex
        return trace_id


class TraceFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = get_trace_id()
        return True
