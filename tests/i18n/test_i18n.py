from pathlib import Path

from peach.i18n.text import ResouceLoader

BASE_DIR = Path(__file__).resolve().parent


def test_i18n():
    res = ResouceLoader(f"{BASE_DIR}/i18n-resource.csv")
    assert res.get_all_lans() == {"zh", "vi", "pt", "en"}
    assert res.get_text("err_1", "zh") == "操作太过频繁，请稍后再试。"
    assert (
        res.get_text("err_1", "en")
        == "The operation is too frequent, please try again later."
    )
    assert res.get_text("err_205", "zh", cd_time=4) == "此礼品码只能 4 后使用"
    assert res.get_text("no_msg_id", "vi") == "no_msg_id"
    assert res.get_text("err_1", "no_lan") == "err_1"
