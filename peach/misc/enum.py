from enum import Enum, IntEnum


class IntCodeEnum(int, Enum):
    """
    扩展内建的 IntEnum 类，在 int 值的基础上加两个字段: code, desc，分别表示该枚举值对应的编码和描述

    Examples:
        class PayType(IntCodeEnum):
            BANK = (1, 'bank', 'payed by bank')
            POINT = (1, 'point', 'payed by point')

    """

    def __new__(cls, value: int, code: str = "", desc: str = ""):
        obj = int.__new__(cls, value)  # type: ignore
        obj._value_ = value
        obj.code = code  # type: ignore
        obj.desc = desc  # type: ignore
        return obj

    @classmethod
    def value_of_code(cls, code):
        """
        Get an enumeration member by `code`.
        :param code:
        :return: An enumeration member mapped to `code`
        """
        for e in cls:
            if e.code == code:
                return e
        raise ValueError(f"code: [{code}] not in {cls.__name__}")


class BroadcastTemplateType(IntEnum):
    GAME = 1  # 游戏
    PYRAMID = 2  # 推广员


class BrandRiskType(IntEnum):
    NEW = 1  # 新增切断
    GAME = 2  # 游戏停服
    WITHDRAW = 4  # 兑换屏蔽
    PAY = 8  # 支付屏蔽
