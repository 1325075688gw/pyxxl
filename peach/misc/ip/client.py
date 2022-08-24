from enum import IntEnum
from ipaddress import ip_address, IPv4Address
from dataclasses import dataclass
import logging
from .ip2location import IP2Location

_LOGGER = logging.getLogger(__name__)


@dataclass
class Location:
    # https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
    country_code: str = "-"
    country_name: str = "-"
    region: str = "-"
    city: str = "-"


class IPType(IntEnum):
    INVALID = 0
    V4 = 1
    V6 = 2


ip_db: IP2Location = None
load_db_err: bool = False


def load_db(path):
    global ip_db, load_db_err
    try:
        ip_db = IP2Location(path)
    except Exception:
        load_db_err = True
        _LOGGER.exception(f"load ip db fail, path: {path}")


def get_location(ip: str) -> Location:
    if not ip_db:
        _LOGGER.error("ip db has not been loaded")
        return Location()

    ip_type = get_ip_type(ip)
    if ip_type == IPType.INVALID:
        _LOGGER.info(f"ip not in db : {ip}")
        return Location()
    elif ip_type == IPType.V6:
        _LOGGER.info(f"ipv6 is not supported : {ip}")
        return Location()

    location = ip_db.get_all(ip)
    return Location(
        country_code=location.country_short,
        country_name=location.country_long,
        region=location.region,
        city=location.city,
    )


def get_ip_type(ip: str) -> IPType:
    try:
        return IPType.V4 if type(ip_address(ip)) is IPv4Address else IPType.V6
    except ValueError:
        return IPType.INVALID
