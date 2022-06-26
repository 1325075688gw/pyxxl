import typing


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
