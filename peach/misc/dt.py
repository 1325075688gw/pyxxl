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


def utc_to_ts(dt):
    """utc时间 to 时间戳"""
    return int(dt.timestamp())


def ts_to_utc(ts):
    """时间戳转utc时间"""
    return datetime.utcfromtimestamp(ts)


def utc_to_local(dt):
    """
    UTC时间转为本地时间
    :param dt: UTC naive时间
    :return:
    """
    if timezone.is_aware(dt):
        return dt.astimezone(LOCAL_TZ)
    return timezone.make_aware(dt, UTC_TZ).astimezone(LOCAL_TZ)


def local_to_utc(dt):
    """local时间 to utc时间"""
    if timezone.is_aware(dt):
        return dt.astimezone(UTC_TZ)
    return timezone.make_aware(dt, LOCAL_TZ).astimezone(UTC_TZ)


def utc_to_local_str(dt, fmt="%Y-%m-%d %H:%M:%S"):
    """UTC naive 时间转本地时间字符串 常用于mongo查询到的时间"""
    if not dt:
        return ""
    return utc_to_local(dt).strftime(fmt)


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
        value = value.replace(tzinfo=timezone.get_current_timezone())
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


def last_month_first_day(local_time=None):
    """
    上月第一天时间
    """
    if not local_time:
        local_time = local_now()
    last_month = 12 if local_time.month == 1 else local_time.month - 1
    last_year = local_time.year - 1 if last_month == 12 else local_time.year
    return timezone.make_aware(datetime(last_year, last_month, 1))


def day_start_time(dt):
    """根据utc时间，得到当天0点的utc时间"""
    local = utc_to_local(dt)
    local_zero = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_to_utc(local_zero)
