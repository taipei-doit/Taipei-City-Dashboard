from datetime import datetime, timedelta

import pytz

TAIPEI_TZ = pytz.timezone("Asia/Taipei")


def get_tpe_now_time(is_with_tz=False):
    """
    This function retrieves the current date and time in Taipei, Taiwan. It offers options to
    include or exclude the timezone information.

    Args:
        is_with_tz (bool, optional): _description_. Defaults to False.

    Example
    ----------
    tpe_now_utc = get_tpe_now_time()
    print(tpe_now_utc)  # Output: For example, 2024-04-26 17:55:00 (without timezone)
    # Output: 2024-04-26 17:56:52
    """
    if is_with_tz:
        return datetime.now(tz=TAIPEI_TZ).replace(microsecond=0)
    else:
        return datetime.now().replace(microsecond=0)


def get_tpe_now_time_str(is_with_tz=False):
    """
    This function retrieves the current date and time in Taipei, Taiwan. It offers options to
    include or exclude the timezone information. The output is a string.

    Args:
        is_with_tz (bool, optional): _description_. Defaults to False.

    Example
    ----------
    tpe_now_utc = get_tpe_now_time_str()
    print(tpe_now_utc)
    print(type(tpe_now_utc))
    # Output: 2024-04-26 17:55:00 (without timezone)
    # Output: <class 'str'>
    """
    if is_with_tz:
        return str(datetime.now(tz=TAIPEI_TZ).replace(microsecond=0))
    else:
        return str(datetime.now().replace(microsecond=0))


def get_tpe_now_time_timestamp(minutes_delta=None):
    """
    Get now time with tz = 'Asia/Taipei'.

    Args:
        minutes_delta: int, default None. If given, will add the minutes_delta to the now time.
    Example
    ----------
    get_tpe_now_time_timestamp()
    # Output: 1648848000000.0
    """

    if minutes_delta:
        now_timestamp = (
            datetime.now(tz=TAIPEI_TZ) + timedelta(minutes=minutes_delta)
        ).timestamp() * 1e3
    else:
        now_timestamp = datetime.now(tz=TAIPEI_TZ).timestamp() * 1e3
    return now_timestamp
