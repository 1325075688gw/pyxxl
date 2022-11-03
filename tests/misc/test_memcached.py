
import time
from peach.misc import memcached

def test_memcached():
    _is_fetch = type("store", (object,), {'value': False})

    _test_data = [1,2,3]
    def _fetch_func():
        _is_fetch.value = True
        return _test_data

    def _query():
        _is_fetch.value = False
        return memcached.get("test_key", fetch_func=_fetch_func, expire_sec=5)
    
    data = _query()
    assert data == _test_data
    assert _is_fetch.value == True

    data = _query()
    assert data == _test_data
    assert _is_fetch.value == False

    time.sleep(6)
    data = _query()
    assert data == _test_data
    assert _is_fetch.value == True
