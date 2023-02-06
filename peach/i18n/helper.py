import decimal
import re
import typing
from typing import Optional
from decimal import Decimal


def get_country(lan: str) -> str:
    # en-IN  --> return IN
    assert lan
    lans = lan.split("-")
    if len(lans) == 2:
        return lans[1]
    return ""


def short_lan(lan: str) -> str:
    # en-IN --> return en
    assert lan
    lans = lan.split("-")
    return lans[0]


def parse_raw_lan(raw_lan: str) -> Optional[str]:
    """
    :param raw_lan: zh-CN,zh;q=0.9 | zh-CN | zh
    :return: zh-CN
    """
    pattern = re.compile(r"^([a-z]{2})(-([A-Z]{2}).*)?")
    result = re.findall(pattern, raw_lan)
    if result:
        matched = result[0]
        lan = matched[0]  # zh
        cn = matched[-1]  # CN
        if cn:
            return f"{lan}-{cn}"
        return lan
    return None


class CommonFormatHelper:
    # 格式化通用规则处理
    def delete_extra_zero(
        self, amount: typing.Union[int, float]
    ) -> typing.Union[int, float]:
        """
        小数点后1//2/3位为0，则不显示为0的部分，例如，
        10.000显示为10，10.00显示为10，
        10.100显示为10.1，10.10显示为10.1，
        10.010显示为10.01，10.01显示为10.01
        """
        if isinstance(amount, float):
            str_amount = str(amount).rstrip("0")
            amount = (
                int(str_amount.rstrip("."))
                if str_amount.endswith(".")
                else float(str_amount)
            )
        return amount

    def format_amount_two_digits(
        self, amount: typing.Union[int, float]
    ) -> typing.Union[int, float, Decimal]:
        amount = self.delete_extra_zero(amount)
        return (
            amount
            if isinstance(amount, int)
            else decimal.Decimal(str(amount)).quantize(
                decimal.Decimal("0.00"), decimal.ROUND_DOWN
            )
        )
