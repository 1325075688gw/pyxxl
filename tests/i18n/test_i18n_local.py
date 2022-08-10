from decimal import Decimal

from peach.i18n.local import format_amount, _format_amount_two_digits


def test_format_credit_by_in():
    amount_k = 100000000
    nation = "en-in"
    di_amount_k = format_amount(amount_k, nation)
    assert di_amount_k == "100K"
    amount_cr = 10827162000.25
    di_amount_cr = format_amount(amount_cr, nation)
    assert di_amount_cr == "1.08Cr"
    di_amount_float = 18897162000.25
    di_amount_float_cr = format_amount(di_amount_float, nation)
    assert di_amount_float_cr == "1.88Cr"
    amount_ = 100000
    di_amount = format_amount(amount_, nation)
    assert di_amount == "100"


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
    amount_m = 1000000000
    di_amount_m = format_amount(amount_m, nation)
    assert di_amount_m == "1M"
    amount_m = 1000000000000
    di_amount_m = format_amount(amount_m, nation)
    assert di_amount_m == "1,000M"
    amount_m_float = 1200323539000
    di_amount_m_float = format_amount(amount_m_float, nation)
    assert di_amount_m_float == "1,200.32M"


def test_format_credit_by_br():
    nation = "pt-br"
    amount_m = 1000000000
    di_amount_m = format_amount(amount_m, nation)
    assert di_amount_m == "1M"
    amount_m_float = 1200323539000
    di_amount_m_float = format_amount(amount_m_float, nation)
    assert di_amount_m_float == "1200.32M"


def test_format_amount_two_digits():
    amount = 10
    assert _format_amount_two_digits(amount) == 10
    amount_float = 50.05
    assert _format_amount_two_digits(amount_float) == Decimal(50.05).quantize(
        Decimal("0.00")
    )
    amount_float1 = 10.00
    assert _format_amount_two_digits(amount_float1) == 10
    amount_float_2 = 10.0
    assert _format_amount_two_digits(amount_float_2) == 10
