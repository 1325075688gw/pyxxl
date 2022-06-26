"""
https://github.com/liut/grpc-retry-py/
"""

import time
import logging

from grpc import StatusCode, UnaryUnaryMultiCallable
from grpc._channel import _InactiveRpcError, _Rendezvous

_LOGGER = logging.getLogger(__name__)

# The maximum number of retries
_MAX_RETRIES_BY_CODE = {
    StatusCode.INTERNAL: 1,
    StatusCode.ABORTED: 2,
    StatusCode.UNAVAILABLE: 2,
    StatusCode.DEADLINE_EXCEEDED: 2,
}

# The minimum seconds (float) of sleeping
_MIN_SLEEPING = 0.015625
_MAX_SLEEPING = 1


class RetriesExceeded(Exception):
    """docstring for RetriesExceeded"""

    pass


def retry(f, transactional=False):
    def wraps(*args, **kwargs):
        retries = 0
        while True:
            try:
                return f(*args, **kwargs)
            except (_InactiveRpcError, _Rendezvous) as e:
                code = e.code()

                max_retries = _MAX_RETRIES_BY_CODE.get(code)
                if max_retries is None or transactional and code == StatusCode.ABORTED:
                    raise

                if retries > max_retries:
                    raise RetriesExceeded(e)

                backoff = min(_MIN_SLEEPING * 2**retries, _MAX_SLEEPING)
                _LOGGER.info(
                    "sleeping %r for %r before retrying failed request...",
                    backoff,
                    code,
                )

                retries += 1
                time.sleep(backoff)

    return wraps


def retrying_stub_methods(obj):
    for key, attr in obj.__dict__.items():
        if isinstance(attr, UnaryUnaryMultiCallable):
            setattr(obj, key, retry(attr))
    return obj
