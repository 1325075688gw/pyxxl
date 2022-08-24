import functools
import logging

import redis
from redis.exceptions import ConnectionError

_LOGGER = logging.getLogger(__name__)

_MAX_TRY_COUNT = 3


class ProxyAgent:
    def __init__(self, **kwargs):
        if kwargs["url"]:
            self.client = redis.StrictRedis.from_url(
                kwargs["url"], decode_responses=True
            )
        else:
            self.client = redis.StrictRedis(
                host=kwargs["host"],
                port=kwargs["port"],
                db=kwargs["db"],
                decode_responses=True,
            )

    def __wrap(self, method, *args, **kwargs):
        try_count = 0
        while try_count < _MAX_TRY_COUNT:
            try:
                f = getattr(self.client, method)
                return f(*args, **kwargs)
            except Exception:
                try_count += 1
                _LOGGER.exception(f"Redis connection fail, try: ({try_count})")
                if try_count >= _MAX_TRY_COUNT:
                    raise ConnectionError(
                        f"Redis connection reached max tries({try_count})"
                    )
                continue

    def __getattr__(self, method):
        return functools.partial(self.__wrap, method)
