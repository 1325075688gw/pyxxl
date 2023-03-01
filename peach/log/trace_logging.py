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


# TODO====================================================后期扩展log，支持通过__LOGGER.info 打印xxl-job日志=================
def get_trace_id_from_xxl_job():
    try:
        from peach.xxl_job.pyxxl.ctx import g2

        xxl_data = g2.xxl_run_data
        trace_id = xxl_data.get("trace_id", None)
        return trace_id
    except Exception as e:
        print(e)
        return None


def get_trace_id_from_otel():
    # 串联 OTel trace id
    otel_trace_id = trace_helper.get_trace_context().trace_id
    if otel_trace_id:
        return hex(otel_trace_id)[2:]  # 转16进制，去掉0x

    try:
        return _LOG_THREAD_VALUE.trace_id
    except AttributeError:
        _LOG_THREAD_VALUE.trace_id = trace_id = uuid.uuid4().hex
        return trace_id


def get_trace_id():
    # 先从xxl-job获取trace_id
    trace_id = get_trace_id_from_xxl_job()
    # 如果xxl-job中没有trace_id，则从otel中获取
    if not trace_id:
        trace_id = get_trace_id_from_otel()
    return trace_id


class TraceFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = get_trace_id()
        return True
