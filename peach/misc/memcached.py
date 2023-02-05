import logging
import typing
from functools import wraps

from django.conf import settings
from pymemcache.client.hash import HashClient
from pymemcache import serde

_LOGGER = logging.getLogger(__name__)

_servers = [e.strip() for e in settings.MEMCACHED_URL.split(",")]
memcached_client = HashClient(
    _servers, serde=serde.pickle_serde, connect_timeout=2, timeout=2, use_pooling=True
)

_enable = settings.MEMCACHED_ENABLE


def cache(key: typing.Union[str, typing.Callable], ex: int = 0):
    """
    key = "online_raffle_confs"
    or
    key = lambda args: "online_raffle_conf:{}".format(args[0])
        args 是传入func的参数

    示例：
    @cache(key=lambda args: "act_conf:{}".format(args[0]))
    def get_conf_by_id(act_id: str) -> ActConfDTO:
        _conf = DActConf.objects(id=act_id).first()
        if not _conf:
            raise BizException(err.ERROR_ACT_CONF_NOT_EXIST)
        return d_act_conf_2_dto(_conf)

    @cache(key=lambda args: "act_conf:{}".format(args[0]))
    def del_conf_by_id(act_id: str) -> ActConfDTO:
       return DActConf.objects(id=act_id).delete()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if not _enable:
                return func(*args, **kwargs)

            cache_key = key if isinstance(key, str) else key(args)
            value, err = _get(cache_key)
            if value is not None:
                return value

            value = func(*args, **kwargs)
            if value is not None:
                _set(cache_key, value, ex)
            return value

        return wrapper
    return decorator


def del_cache(key: typing.Union[str, typing.Callable], del_func: typing.Callable):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            cache_key = key if isinstance(key, str) else key(args)
            del_func(cache_key)
            return result

        return wrapper
    return decorator


def get(
    key: str, fetch_func: typing.Callable[[], typing.Any] = None, expire_sec: int = 0
):
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
            _set(key, value, expire_sec)
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


def _set(key, value, expire_sec=0):
    try:
        memcached_client.set(key, value, expire=expire_sec)
    except Exception:
        _LOGGER.exception(f"Memcached Set Fail: {key}")
