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
