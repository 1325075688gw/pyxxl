import logging
import typing

from django.conf import settings
from pymemcache.client.hash import HashClient
from pymemcache import serde

_LOGGER = logging.getLogger(__name__)

_servers = [e.strip() for e in settings.MEMCACHED_URL.split(",")]
memcached_client = HashClient(
    _servers, serde=serde.pickle_serde, connect_timeout=2, timeout=2, use_pooling=True
)

_enable = settings.MEMCACHED_ENABLE


def get(key: str, fetch_func: typing.Callable[[], typing.Any] = None):
    """
    get cached value by key and return it if it exists, otherwise,
    get the value by 'fetch_func' and set it into the cache.
    """
    if not _enable:
        return fetch_func()

    value, err = _get(key)
    if value is not None:
        return value
    if fetch_func:
        value = fetch_func()
        if value is not None:
            _set(key, value)
    return value


def delete(key: str):
    if not _enable:
        return

    try:
        memcached_client.delete(key)
    except Exception:
        _LOGGER.exception(f"Memcached Delete Fail: {key}")


def _get(key: str):
    """
    return (value, err)
    """
    try:
        value = memcached_client.get(key)
        return value, None
    except Exception as ex:
        _LOGGER.exception(f"Memcached Get Fail: {key}")
        return None, ex


def _set(key, value):
    try:
        memcached_client.set(key, value)
    except Exception:
        _LOGGER.exception(f"Memcached Set Fail: {key}")
