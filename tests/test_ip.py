from pathlib import Path
from peach.misc import ip


DEFAULT_NAME = "-"

BASE_DIR = Path(__file__).resolve().parent


def test_get_ip():
    location = ip.get_location("1.0.63.215")
    assert location.country_code == DEFAULT_NAME
    ip.load_db(f"{BASE_DIR}/IP-COUNTRY.BIN")
    location = ip.get_location("1.0.63.215")
    assert location.country_code == "CN"
    assert ip.get_ip_type("1.0.63.215") == ip.IPType.V4
    assert ip.get_ip_type("2002:0000:0000:1234:abcd:ffff:c0a8:0000") == ip.IPType.V6
    assert ip.get_ip_type("1.2.33.34a") == ip.IPType.INVALID
