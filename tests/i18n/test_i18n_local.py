from peach.i18n.local import format_amount


def test_format_credit_by_hi():
    amount_k = 100000000
    nation = "hi"
    di_amount_k = format_amount(amount_k, nation)
    assert di_amount_k == "100K"
    amount_cr = 10827162000.25
    di_amount_cr = format_amount(amount_cr, nation)
    assert di_amount_cr == "1.08Cr"


def test_format_credit_by_vi():
    amount_k = 100000000
    nation = "vi"
    di_amount_k = format_amount(amount_k, nation)
    assert di_amount_k == "100K"
    amount_m = 1000000000
    di_amount_m = format_amount(amount_m, nation)
    assert di_amount_m == "1M"


def test_format_credit_by_id():
    nation = "id"
    amount_m = 1000000000
    di_amount_m = format_amount(amount_m, nation)
    assert di_amount_m == "1M"
    amount_m = 1000000000000
    di_amount_m = format_amount(amount_m, nation)
    assert di_amount_m == "1,000M"
    amount_m_float = 1200323539000
    di_amount_m_float = format_amount(amount_m_float, nation)
    assert di_amount_m_float == "1,200.32M"


def test_format_credit_by_pt():
    nation = "pt"
    amount_m = 1000000000
    di_amount_m = format_amount(amount_m, nation)
    assert di_amount_m == "1M"
    amount_m_float = 1200323539000
    di_amount_m_float = format_amount(amount_m_float, nation)
    assert di_amount_m_float == "1200.32M"
