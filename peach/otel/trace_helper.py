from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


def trace_exception(ex: Exception):
    """记录异常"""
    current_span = trace.get_current_span()
    current_span.set_status(Status(StatusCode.ERROR))  # trace span 标记为失败
    current_span.record_exception(ex)  # 记录异常信息


def trace_data(**data):
    """记录数据"""
    current_span = trace.get_current_span()
    current_span.set_attributes(data)


def get_trace_context():
    """获取 trace 上下文"""
    current_span = trace.get_current_span()
    return current_span.get_span_context()


# def trace_set_baggage(**data):
#     """设置 baggage"""
#     for key, value in data.items():
#         baggage.set_baggage(key, value)
#
#
# def trace_get_baggage(key):
#     """获取 baggage"""
#     return baggage.get_baggage(key)
