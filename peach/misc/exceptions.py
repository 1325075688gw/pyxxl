import typing
import logging
from functools import wraps, partial
from inspect import getfullargspec


class BizErrorCode:
    def __init__(self, code: int, message: str = None):
        self.code = code
        self.message = message

    def __hash__(self):
        return self.code

    def __eq__(self, other):
        if not isinstance(other, BizErrorCode):
            return False
        return other.code == self.code


class BizException(Exception):
    def __init__(self, error_code: typing.Union[int, BizErrorCode], message=None):
        if isinstance(error_code, int):
            error_code = BizErrorCode(error_code, message)
        self.error_code = error_code
        if message:
            self.error_code.message = message
        super().__init__(
            "code: {}, message: {}".format(error_code.code, error_code.message)
        )

    def __str__(self):
        return f"code: {self.error_code.code}, msg: {self.error_code.message}"


class IllegalRequestException(Exception):
    pass


def no_exception(func=None, biz_exc: BizException = None):
    """
    捕获程序异常并打印日志
    使用场景：出现异常后不影响程序正常向后运行
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            params = getfullargspec(func).args
            args_fields = params[: len(args)]
            kwargs.update(dict(zip(args_fields, args)))  # 全部转换成关键字参数

            logging.exception(
                f"<exception catch>: {func.__name__} occur error: {str(e)}, params: {kwargs}!"
            )
            if biz_exc:
                raise biz_exc
            return None

    if func is None:
        return partial(no_exception, bizExc=biz_exc)
    return wrapper
