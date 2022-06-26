from datetime import datetime, timedelta

from django.utils import timezone

LOCAL_TZ = timezone.get_current_timezone()
UTC_TZ = timezone.utc


def today():
    return at_start_of_day(timezone.localtime())


def today_str():
    return local_now().strftime("%Y-%m-%d")


def yesterday():
    return today() - timedelta(days=1)


def tomorrow():
    return today() + timedelta(days=1)


def local_now():
    """获取当前本地时间"""
    return timezone.localtime()


def now_ts():
    """获取当前时间戳"""
    return int(timezone.now().timestamp())


def now_mts():
    return int(timezone.now().timestamp() * 1000)


def as_ts(time: datetime):
    return int(time.timestamp())


def as_mts(time: datetime):
    return int(time.timestamp() * 1000)


def utc_to_local(dt):
    """
    UTC时间转为本地时间
    :param dt: UTC naive时间
    :return:
    """
    if timezone.is_aware(dt):
        return dt.astimezone(LOCAL_TZ)
    return timezone.make_aware(dt, UTC_TZ).astimezone(LOCAL_TZ)


def parse_datetime(date_string: str) -> datetime:
    """
    将日期格式字符串转换成日期对象, 且时区为当前设置时区
    """
    fmts = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
    value = None
    for fmt in fmts:
        try:
            value = datetime.strptime(date_string, fmt)
            break
        except ValueError:
            continue
    if value is None:
        raise ValueError(f"date_string must be match any format of: {fmts}")
    if not value.tzinfo:
        value = timezone.get_current_timezone().localize(value)
    return value


def from_timestamp(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())


def at_start_of_day(time: datetime) -> datetime:
    """
    获取日期参数'time'的0点开始时间对象。
    :return:
    """
    if not time.tzinfo:
        time = timezone.get_current_timezone().localize(time)

    return time.replace(hour=0, minute=0, second=0, microsecond=0)


def at_start_of_hour(time: datetime) -> datetime:
    """
    获取日期参数`time`当前小时0分开始的时间对象
    """
    if not time.tzinfo:
        time = timezone.get_current_timezone().localize(time)
    return time.replace(minute=0, second=0, microsecond=0)


def at_start_of_week(time: datetime) -> datetime:
    """
    获取日期参数`time`所在`周`的第一天
    """
    t = at_start_of_day(time)
    return t - timedelta(days=(t.weekday() + 1) % 7)


def at_start_of_month(time: datetime) -> datetime:
    """
    获取日期参数`time`所在`月`的第一天
    """
    t = at_start_of_day(time)
    return t.replace(day=1)
