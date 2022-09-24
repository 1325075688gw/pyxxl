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
    :param raw_lan: zh-CN,zh;q=0.9
    :return: zh-CN
    """
    pattern = re.compile(r"^([a-z]{2}-[A-Z]{2}).*")
    result = re.findall(pattern, raw_lan)
    if result:
        return result[0]
    return None
