import decimal
from datetime import datetime
from decimal import Decimal
from functools import partial

from peach.i18n.helper import get_country
from peach.misc.util import singleton

# 展示单位M, K, Cr的阈值
_TO_M = 1000000
_TO_CR = 10000000
_TO_K = 1000

# 基本单位
_M = 1000000
_K = 1000
_CR = 10000000

GAME_AMOUNT_RATIO = 1000  # 厘


def format_datetime(dt: datetime, lan: str) -> str:
    assert isinstance(dt, datetime)
    assert isinstance(lan, str)
    if lan in ["pt", "hi", "id"]:
        return dt.strftime("%d-%m-%Y %H:%M:%S")
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_amount(
    amount: int or float,
    lan: str,
) -> str:
    assert isinstance(amount, (int, float))
    assert lan
    country = get_country(lan).upper()
    if country == "BR":
        convert_tool = BRFormatter()
    elif country == "IN":
        convert_tool = INFormatter()
    elif country == "ID":
        convert_tool = IDFormatter()
    elif country == "VN":
        convert_tool = VNFormatter()
    else:
        convert_tool = CommonFormatter()
    return convert_tool.convert_amount(_divide_amount(amount))


class BaseFormatter:
    def convert_amount(self, amount: int or float) -> str:
        raise NotImplementedError()


@singleton
class CommonFormatter(BaseFormatter):
    def convert_amount(self, amount: int or float) -> str:
        return str(amount)


@singleton
class BRFormatter(BaseFormatter):
    # 巴西邮件金额格式化
    def convert_amount(self, amount: int or float) -> str:
        if amount >= _TO_M:
            m_amount = amount / _M
            if m_amount == int(m_amount):
                amount = f"{int(m_amount)}M"
            else:
                amount = f"{_format_amount_two_digits(m_amount)}M"
            return amount
        return str(_format_amount_two_digits(amount))


@singleton
class IDFormatter(BaseFormatter):
    # 印尼邮件金额格式化
    def convert_amount(self, amount: int or float) -> str:
        if amount >= _TO_M:
            m_amount = amount / _M
            if m_amount == int(m_amount):
                amount = f"{format(int(m_amount), ',')}M"
            else:
                amount = f"{format(_format_amount_two_digits(m_amount), ',')}M"
            return amount
        return str(_format_amount_two_digits(amount))


@singleton
class INFormatter(BaseFormatter):
    # 印度邮件金额格式化
    def convert_amount(self, amount: int or float) -> str:
        if _TO_K < amount >= _TO_CR:
            return f"{_format_amount_two_digits(amount / _CR)}Cr"
        elif _TO_K <= amount < _TO_CR:
            k_amount = _format_amount_two_digits(amount / _K)
            if k_amount == int(k_amount):
                amount = f"{int(k_amount)}K"
            else:
                amount = f"{k_amount}K"
            return amount
        else:
            return str(_format_amount_two_digits(amount))


@singleton
class VNFormatter(BaseFormatter):
    # 越南邮件金额格式化
    def convert_amount(self, amount: int or float) -> str:
        if amount >= _TO_M:
            return f"{int(amount / _M)}M"
        elif _TO_K <= amount < _TO_M:
            return f"{int(amount / _K)}K"
        return str(_format_amount_two_digits(amount))


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


def _format_amount_two_digits(amount: float or int) -> int or Decimal:
    if isinstance(amount, int):
        return amount
    elif int(amount) == amount:
        return int(amount)
    else:
        return decimal.Decimal(str(amount)).quantize(
            decimal.Decimal("0.00"), decimal.ROUND_DOWN
        )
