import re
from typing import Optional


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
