import datetime
from decimal import Decimal

from peach.i18n.helper import CommonFormatHelper
from peach.i18n.local import format_amount, format_datetime


def test_format_credit_by_in():
    nation = "en-in"
    amount_cr = 10827162000.25
    di_amount_cr = format_amount(amount_cr, nation)
    assert di_amount_cr == "1.08Cr"
    di_amount_float = 18897162000.25
    di_amount_float_cr = format_amount(di_amount_float, nation)
    assert di_amount_float_cr == "1.88Cr"
    amount_ = 100000
    di_amount = format_amount(amount_, nation)
    assert di_amount == "100"
    assert format_amount(101300.0, nation) == "101.30"
    assert format_amount(101000.0, nation) == "101"
    assert format_amount(101376.0, nation) == "101.37"


def test_format_credit_by_vn():
    amount_k = 100000000
    nation = "vi-vn"
    di_amount_k = format_amount(amount_k, nation)
    assert di_amount_k == "100K"
    amount_m = 1000000000
    di_amount_m = format_amount(amount_m, nation)
    assert di_amount_m == "1M"


def test_format_credit_by_id():
    nation = "id-id"
    amount = 100000.01999999
    assert format_amount(amount, nation) == "100"
    amount = 10000
    assert format_amount(amount, nation) == "10"
    amount = 1000000.02
    assert format_amount(amount, nation) == "1K"
    amount = 1002000.02
    assert format_amount(amount, nation) == "1K"
    amount = 102450000.88
    assert format_amount(amount, nation) == "102.45K"
    amount = 98100000.34
    assert format_amount(amount, nation) == "98.1K"
    amount = 1000000000
    assert format_amount(amount, nation) == "1M"
    amount = 1000000000.02
    assert format_amount(amount, nation) == "1M"
    amount = 1634000000.02
    assert format_amount(amount, nation) == "1.634M"
    amount = 1634000000000.02
    assert format_amount(amount, nation) == "1,634M"


def test_format_credit_by_br():
    nation = "pt-br"
    amount_lt_k = 99934.6895
    assert format_amount(amount_lt_k, nation) == "99.934"

    amount_gt_k = 9993464.6895
    assert format_amount(amount_gt_k, nation) == "9993.46"

    amount1 = 10000.0000
    assert format_amount(amount1, nation) == "10"

    amount2 = 10000.0
    assert format_amount(amount2, nation) == "10"

    amount3 = 10100.0
    assert format_amount(amount3, nation) == "10.1"

    amount4 = 10010.0
    assert format_amount(amount4, nation) == "10.01"

    amount_m = 1000000000
    di_amount_m = format_amount(amount_m, nation)
    assert di_amount_m == "1M"
    amount_m_float = 1200323539000
    di_amount_m_float = format_amount(amount_m_float, nation)
    assert di_amount_m_float == "1200.323M"


def test_format_amount_two_digits():
    amount = 10
    format_helper = CommonFormatHelper()
    assert format_helper.format_amount_two_digits(amount) == 10
    amount_float = 50.05
    assert format_helper.format_amount_two_digits(amount_float) == Decimal(
        50.05
    ).quantize(Decimal("0.00"))
    amount_float1 = 10.00
    assert format_helper.format_amount_two_digits(amount_float1) == 10
    amount_float_2 = 10.0
    assert format_helper.format_amount_two_digits(amount_float_2) == 10


def test_format_datetime():
    lan = "pt-br"
    data_time = datetime.datetime.now()
    format_date_time = format_datetime(data_time, lan)
    assert format_date_time == data_time.strftime("%d-%m-%Y %H:%M:%S")
    lan = "in"
    format_date_time = format_datetime(data_time, lan)
    assert format_date_time == data_time.strftime("%Y-%m-%d %H:%M:%S")


def test_format_amount_0_in_after():
    format_helper = CommonFormatHelper()
    assert format_helper.delete_extra_zero(100.00) == 100
