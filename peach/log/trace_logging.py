import logging
import threading
import uuid

_LOG_THREAD_VALUE = threading.local()


def clear_trace():
    try:
        del _LOG_THREAD_VALUE.trace_id
    except AttributeError:
        pass


def get_trace_id():
    try:
        return _LOG_THREAD_VALUE.trace_id
    except AttributeError:
        _LOG_THREAD_VALUE.trace_id = trace_id = uuid.uuid4().hex
        return trace_id


class TraceFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = get_trace_id()
        return True
