import time
from peach.misc import memcached
from peach.misc.memcached import cache, del_cache, delete


def test_cache_decorator():
    _is_fetch = type("store", (object,), {"value": True})

    _test_data = [1, 2, 3]

    # test key is str
    @cache("_test_datas")
    def _query_datas():
        _is_fetch.value = True
        return _test_data

    # 清除缓存
    memcached.delete("_test_datas")

    # 第一次不走缓存
    data = _query_datas()
    assert data == _test_data
    assert _is_fetch.value is True
    # 第二次走缓存
    _is_fetch.value = False
    data = _query_datas()
    assert data == _test_data
    assert _is_fetch.value is False

    # test key is lambda func
    @cache(key=lambda args: "_test_data:{}".format(args[0]))
    def _query_data(idx):
        _is_fetch.value = True
        return _test_data[idx]

    # 第一次不走缓存
    memcached.delete("_test_data:0")
    data = _query_data(0)
    assert data == _test_data[0]
    assert _is_fetch.value is True
    # 第二次走缓存
    _is_fetch.value = False
    data = _query_data(0)
    assert data == _test_data[0]
    assert _is_fetch.value is False

    @del_cache(key=lambda args: "_test_data:{}".format(args[0]), del_func=delete)
    def _del_data(idx):
        return

    # 写入缓存
    _query_data(0)

    # 第一次不走缓存
    _del_data(0)
    data = _query_data(0)
    assert data == _test_data[0]
    assert _is_fetch.value is True
    # 第二次次走缓存
    _is_fetch.value = False
    data = _query_data(0)
    assert data == _test_data[0]
    assert _is_fetch.value is False


def test_memcached():
    _is_fetch = type("store", (object,), {"value": False})

    _test_data = [1, 2, 3]

    def _fetch_func():
        _is_fetch.value = True
        return _test_data

    def _query():
        _is_fetch.value = False
        return memcached.get("test_key", fetch_func=_fetch_func, expire_sec=5)

    memcached.delete("test_key")

    data = _query()
    assert data == _test_data
    assert _is_fetch.value is True

    time.sleep(1)
    data = _query()
    assert data == _test_data
    assert _is_fetch.value is False

    time.sleep(5)
    data = _query()
    assert data == _test_data
    assert _is_fetch.value is True
