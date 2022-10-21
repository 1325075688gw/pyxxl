from pathlib import Path

from peach.i18n import helper
from peach.i18n.text import ResourceLoader, SourceType

BASE_DIR = Path(__file__).resolve().parent


def test_i18n():
    res = ResourceLoader(f"{BASE_DIR}/i18n-resource.csv")
    assert res.get_all_lans() == {"zh", "vi", "pt", "en"}
    assert res.get_text("err_1", "zh") == "操作太过频繁，请稍后再试。"
    assert (
        res.get_text("err_1", "en")
        == "The operation is too frequent, please try again later."
    )
    assert res.get_text("err_205", "zh", cd_time=4) == "此礼品码只能 4 后使用"
    assert res.get_text("no_msg_id", "vi") == "no_msg_id"
    assert res.get_text("err_1", "no_lan") == "err_1"


def test_i18n_from_content():
    source = """Module,msg_id,zh,en,vi,pt
Sys(系统),err_1,操作太过频繁，请稍后再试。,"The operation is too frequent, please try again later.",,
Account(账户),err_100,网络错误或帐号在其他设备上登录，请重新登录,,,
,err_101,密码错误,,,
,err_102,账号错误，请联系客服中心,,,
,err_103,帐号不存在,,,
,err_104,验证码错误,,,
,err_105,请用正式账号登录,,,
,err_106,服务已下线,,,
,err_107,此IP创建帐户已达到限制,,,
,err_108,此设备上创建帐户已达到限制,,,
,err_109,此帐户已被注册,,,
Asset(资产),err_500,保险箱余额不足,,,
,err_501,余额不足,,,
Exchange(兑换码),err_200,改兑换码以兑换，请勿重复兑换,,,
,err_201,兑换码已过期,,,
,err_202,兑换码缺货，请联系客服,,,
,err_203,您的兑换次数已达上限，将机会留给他人！,,,
,err_204,兑换活动还未开始，请耐心等待,,,
,err_205,此礼品码只能 {cd_time} 后使用,,,
Mail(邮件),err_300,邮件附件已领取，请勿重复领取,,,
,err_301,礼包过期了，下次记得马上领取哦~,,,
Props(道具),err_400,礼品缺货，请联系客服,,,
Game(游戏),err_600,此游戏正在维护中,,,
,err_601,此游戏正在开发中,,,
Activity(活动),err_700,活动尚未开始，请耐心等待,,,
Withdraw(提现),err_800,绑定账号数量超过上限,,,
,err_801,提现服务暂时不可以，请稍后重试,,,
,err_802,抱歉，您正在游戏中，请稍后重试,,,
,err_803,抱歉，提现前请您注册正式账号,,,
,err_804,请分钟{cd_time}后更改提款方式或提取更多余额,,,"""
    res = ResourceLoader(source, SourceType.CONTENT)
    assert res.get_all_lans() == {"zh", "vi", "pt", "en"}
    assert res.get_text("err_1", "zh") == "操作太过频繁，请稍后再试。"
    assert (
        res.get_text("err_1", "en")
        == "The operation is too frequent, please try again later."
    )
    assert res.get_text("err_205", "zh", cd_time=4) == "此礼品码只能 4 后使用"
    assert res.get_text("no_msg_id", "vi") == "no_msg_id"
    assert res.get_text("err_1", "no_lan") == "err_1"


def test_parse_raw_lan():

    raw_lan = "zh"
    lan = helper.parse_raw_lan(raw_lan)
    assert lan == "zh"

    raw_lan = "zh-CN"
    lan = helper.parse_raw_lan(raw_lan)
    assert lan == "zh-CN"

    raw_lan = "zh-CN,zh;q=0.9"
    lan = helper.parse_raw_lan(raw_lan)
    assert lan == "zh-CN"

    raw_lan = "Zh-CN,zh;q=0.9"
    lan = helper.parse_raw_lan(raw_lan)
    assert not lan

    raw_lan = "zh-cn,zh;q=0.9"
    lan = helper.parse_raw_lan(raw_lan)
    assert lan == "zh"
