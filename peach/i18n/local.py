# mypy: ignore-errors
import math
import typing
from datetime import datetime
from decimal import Decimal
from functools import partial

from peach.i18n.helper import get_country, CommonFormatHelper
from peach.misc.util import singleton

# 展示单位M, K, Cr的阈值
_TO_M = 1000000
_TO_CR = 10000000
_TO_K = 1000

# 基本单位
_M = 1000000
_CR = 10000000
_K = 1000

GAME_AMOUNT_RATIO = 1000  # 厘


def format_datetime(dt: datetime, lan: str) -> str:
    assert isinstance(dt, datetime)
    format_handler = _get_format_handler(lan)
    return format_handler.format_datetime(dt)


def format_amount(
    amount: typing.Union[int, float],
    lan: str,
) -> str:
    assert isinstance(amount, (int, float))
    format_handler = _get_format_handler(lan)
    return format_handler.format_amount(_divide_amount(amount))


class BaseFormatHandler:
    def format_amount(self, amount: typing.Union[int, float]) -> str:
        raise NotImplementedError()

    def format_datetime(self, dt: datetime) -> str:
        raise NotImplementedError()


@singleton
class CommonFormatHandler(BaseFormatHandler):
    def format_amount(self, amount: typing.Union[int, float]) -> str:
        return str(amount)

    def format_datetime(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


@singleton
class BRFormatHandler(BaseFormatHandler, CommonFormatHelper):
    def format_amount(self, amount: typing.Union[int, float]) -> str:
        if amount < _TO_K:
            amount = math.floor(amount * 10**3) / 10**3
        elif amount >= _TO_M:
            amount = math.floor(amount / _M * 10**3) / 10**3
            return f"{self.delete_extra_zero(amount)}M"
        elif amount >= _TO_K:
            amount = math.floor(amount * 10**2) / 10**2
        return str(self.delete_extra_zero(amount))

    def format_datetime(self, dt: datetime) -> str:
        return dt.strftime("%d-%m-%Y %H:%M:%S")


@singleton
class IDFormatHandler(BaseFormatHandler, CommonFormatHelper):
    def format_amount(self, amount: typing.Union[int, float]) -> str:
        # 印尼在转换k和m之前先把小数舍弃掉, 不做四舍五入
        amount = int(amount)
        if amount >= _TO_M:
            amount = math.floor(amount / _M * 10**3) / 10**3
            return f"{format(self.delete_extra_zero(amount), ',')}M"
        elif amount >= _TO_K:
            amount = math.floor(amount / _K * 10**2) / 10**2
            return f"{format(self.delete_extra_zero(amount), ',')}K"
        return str(amount)

    def format_datetime(self, dt: datetime) -> str:
        return dt.strftime("%d-%m-%Y %H:%M:%S")


@singleton
class INFormatHandler(BaseFormatHandler, CommonFormatHelper):
    def format_amount(self, amount: typing.Union[int, float]) -> str:
        if amount >= _TO_CR:
            return f"{self.format_amount_two_digits(amount / _CR)}Cr"
        else:
            return str(self.format_amount_two_digits(amount))

    def format_datetime(self, dt: datetime) -> str:
        return dt.strftime("%d-%m-%Y %H:%M:%S")


@singleton
class VNFormatHandler(BaseFormatHandler, CommonFormatHelper):
    def format_amount(self, amount: typing.Union[int, float]) -> str:
        if amount >= _TO_M:
            return f"{int(amount / _M)}M"
        elif _TO_K <= amount < _TO_M:
            return f"{int(amount / _K)}K"
        return str(self.format_amount_two_digits(amount))

    def format_datetime(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def _convert_amount(d, method, keys):
    """
    将数据d或数据d中指定的字段使用method方法转换
    :param d: 数据
    :param method: 转换方法
    :param keys: 指定keys
    :return:
    """
    if isinstance(d, (int, float, Decimal)):
        return method(d)
    return d


def _divide_amount(d, *keys):
    """
    将数据中指定键的数值或者int/float / 1000
    :param d: 字典或者包含字典的列表
    :param keys: 指定的处理字断
    :return:
    """
    return _convert_amount(
        d, partial(divide_amount_to_ratio, ratio=GAME_AMOUNT_RATIO), keys
    )


def divide_amount_to_ratio(x, ratio):
    return x / ratio


def _get_format_handler(lan: str):
    assert lan
    country = get_country(lan).upper()
    if country == "BR":
        format_handler = BRFormatHandler()
    elif country == "IN":
        format_handler = INFormatHandler()
    elif country == "ID":
        format_handler = IDFormatHandler()
    elif country == "VN":
        format_handler = VNFormatHandler()
    else:
        format_handler = CommonFormatHandler()
    return format_handler
