from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from functools import partial

GAME_CREDIT_RATIO = 1000  # 厘


def _utc_to_local(dt):
    """
    UTC时间转为本地时间
    :param dt: UTC naive时间
    :return:
    """
    if timezone.is_aware(dt):
        return dt.astimezone(timezone.get_current_timezone())
    return timezone.make_aware(dt, timezone.utc).astimezone(
        timezone.get_current_timezone()
    )


def divide_credit_atomic(x, ratio):
    return x / ratio


def _convert_credit(d, method, keys):
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


def _divi_credit(d, *keys):
    """
    将数据中指定键的数值或者int/float / 1000
    :param d: 字典或者包含字典的列表
    :param keys: 指定的处理字断
    :return:
    """
    return _convert_credit(
        d, partial(divide_credit_atomic, ratio=GAME_CREDIT_RATIO), keys
    )


def _format_credit(amount):
    """
    针对邮件使用金额转换
    :param amount: 邮件内展示的金额，单位：厘
    :return:
    """
    return _divi_credit(amount)


def format_email_dt_amount(
    format_txt, dt: datetime = None, amount: int = None, **kwargs
):
    """
    转换邮件内容中的时间和钱
    """
    if dt:
        kwargs["dt"] = _utc_to_local(dt).strftime("%Y-%m-%d %H:%M:%S")
    if amount:
        kwargs["amount"] = _format_credit(amount)

    return format_txt.format(**kwargs)
