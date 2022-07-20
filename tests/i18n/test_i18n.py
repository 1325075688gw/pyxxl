from pathlib import Path

from peach.i18n.text import ResouceLoader

BASE_DIR = Path(__file__).resolve().parent


def test_i18n():
    res = ResouceLoader(f"{BASE_DIR}/i18n-resource.csv")
    assert res.get_all_lans() == {"zh", "vi", "pt", "en"}
    assert res.get_text("err_01", "zh") == "您的账号已被禁止使用"
    assert res.get_text("err_01", "vi") == "Tài khoản của bạn đã bị cấm"
    assert res.get_text("err_02", "zh", vip_level=4) == '恭喜您升到 "4" 级, 请查收您的特权'
    assert res.get_text("no_msg_id", "vi") == "no_msg_id"
    assert res.get_text("err_01", "no_lan") == "err_01"
