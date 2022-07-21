from peach.misc.exceptions import BizErrorCode, BizException


def test_exception():
    err = BizException(1)
    assert err.error_code.code == 1
    assert err.error_code.message is None

    err = BizException(1, "hello")
    assert err.error_code.code == 1
    assert err.error_code.message == "hello"

    err = BizException(1, "hello, {name}", name="world")
    assert err.error_code.code == 1
    assert err.error_code.message == "hello, world"

    code = BizErrorCode(2)
    err = BizException(code, name="world")
    msg = "hello, {name}"
    assert err.error_code.code == 2
    assert err.error_code.message is None
    assert msg.format(**err.params) == "hello, world"
