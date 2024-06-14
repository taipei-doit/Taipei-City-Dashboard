import re
from datetime import datetime
from math import isinf

import pandas as pd
import pytz
from numpy import nan

TAIPEI_TZ = pytz.timezone("Asia/Taipei")


def omit_chinese_string_in_time(x: str):
    """
    Process time column with Chinese string like "上午" or "下午", and even ".000" at the end.

    Example
    ----------
    omit_chinese_string_in_time(None)
    omit_chinese_string_in_time("2022/7/14 上午 12:00:00")
    omit_chinese_string_in_time("2022/7/14 下午 12:00:00")
    omit_chinese_string_in_time("2022/7/14 下午 12:00:00.000")
    # Output: '2022-07-14 12:00:00'
    # Output: '2022-07-14 00:00:00'
    # Output: '2022-07-14 12:00:00'
    """
    if x:
        x = x.replace(".000", "")
        x = x.replace("  ", " ")
        split_x = x.split(" ")
        if split_x[1] == "上午":
            hour = int(split_x[2][0:2])
            if hour == 12:  # 上午12=00點
                fine_x = split_x[0] + " " + "00" + split_x[2][2:]
            else:  # 不用轉換
                fine_x = split_x[0] + " " + split_x[2]
        elif split_x[1] == "下午":
            hour = int(split_x[2][0:2]) + 12  # 下午 = +12
            if hour == 24:  # 下午12點=12點
                hour = 12
            fine_x = split_x[0] + " " + str(hour) + split_x[2][2:]
        else:
            # print(x)
            pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
            if re.match(pattern, x)[0]:
                fine_x = x
            else:
                fine_x = re.findall(pattern, x)[0]
        return fine_x
    else:
        return None


def _convert_inf_to_nan(series: pd.Series) -> pd.Series:
    """
    Check if there is inf in the series, and convert it to None.
    Because inf is not supported in pd.to_datetime.

    Example
    ----------
    _convert_inf_to_nan(pd.Series(['2023/12/12', None, float('-inf'), float('inf')]))
    """
    is_inf = series.apply(lambda x: isinstance(x, float) and isinf(x))
    is_na = pd.isna(series)
    is_empty_str = series == ""
    is_invalid = is_na | is_empty_str | is_inf
    if any(is_invalid):
        series.loc[is_invalid] = nan
    return series


def _minguo_calendar_to_gregorian(
    time_column: pd.Series, format_str: str, ty_pattern: str = "%TY"
):
    """
    Convert Minguo calendar string to Gregorian calendar string. Minguo calendar is a calendar used
    in Taiwan, which is the Gregorian calendar with the year minus 1911. For example, 2021 in
    Gregorian calendar is 110 in Minguo calendar.

    Args
    -----
    time_column: pandas.Series, the column to be converted, with dtype str.
    format_str: str, the format string of the time_column.
    ty_pattern: str, the pattern of the year in Minguo calendar. Default is '%TY'.

    Example
    ----------
    time_column = pd.Series(['1101230', '1101231'])
    format_str = '%TY%m%d'
    tc, fs = _minguo_calendar_to_gregorian(time_column, format_str)
    print(tc)
    print(fs)
    # Output:
    # >>> print(tc)
    # 0    20211230
    # 1    20211231
    # dtype: object
    # >>> print(fs)
    # %Y%m%d

    time_column = pd.Series(['12/30/110', '12/31/110', nan])
    format_str = '%m/%d/%TY'
    tc, fs = _minguo_calendar_to_gregorian(time_column, format_str)
    print(tc)
    # >>> print(tc)
    # 0    12/30/2021
    # 1    12/31/2021
    # 2           NaN
    # dtype: object
    print(fs)
    # >>> print(fs)
    # %m/%d/%Y
    """
    if ty_pattern in format_str:
        is_ty_at_start = format_str.startswith(ty_pattern)
        is_ty_at_end = format_str.endswith(ty_pattern)

        is_str = time_column.apply(lambda x: isinstance(x, str))
        # skip value that is not string
        time_column_only_str = time_column.loc[is_str]
        if is_ty_at_start:
            minguo_year = time_column_only_str.str[:3]
            gregorian_year = (minguo_year.astype(int) + 1911).astype(str)
            time_column_only_str = gregorian_year + time_column_only_str.str[3:]
        elif is_ty_at_end:
            minguo_year = time_column_only_str.str[-3:]
            gregorian_year = (minguo_year.astype(int) + 1911).astype(str)
            time_column_only_str = time_column_only_str.str[:-3] + gregorian_year
        else:
            raise ValueError("Can not process %TY in the middle of the format string")
        time_column.loc[is_str] = time_column_only_str

    return time_column, format_str.replace("TY", "Y")


def _get_offset_hour(timezone: str) -> int:
    """
    Get the UTC offset hours of a given timezone.

    Args
    -----
    timezone: str, the timezone name.
        All timezone names can be found in pytz.all_timezones.

    Example
    ----------
    _get_offset_hour('Asia/Taipei')
    # Output:
    # '+08:00'
    _get_offset_hour('Pacific/Pago_Pago')
    # Output:
    # '-11:00'
    """
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    offset_hours = int(now.utcoffset().total_seconds() / 3600)
    return f"{int(offset_hours):+03}:00"


def convert_str_to_time_format(
    time_column: pd.Series,
    from_format=None,
    output_level="datetime",
    output_type="time",
    is_from_utc=False,
    from_timezone="Asia/Taipei",
    to_timezone="Asia/Taipei",
    is_omit_microsecond=True,
    errors="raise",
) -> pd.Series:
    """
    A time processing function for Taiwan time zone.
    This is a high-level API for pd.to_datetime, enhanced with the capability to handle the Minguo-
    calendar and incorporate a mechanism to apply a +8 time zone offset. Minguo calendar is the
    official calendar in Taiwan, which is the Gregorian calendar with the year minus 1911.
    '%TY' (Taiwan year) is used to represent the year of Minguo calendar, should be [0-9]{3}.

    Parameters
    ----------
    output_level: "date" or "datetime", default "datetime".
    output_type: "str" or "time", default "time".
    from_format: Default is None, indicating a common format. In this case, the function will
        automatically parse the input. Alternatively, you can provide a string like "%TY/%m/%d" or
        "%Y%m%d" in specific format. All format codes can be found in
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior.
        The only difference is that the year in Minguo calendar should be represented by '%TY'
        instead of '%Y'.
    is_from_utc: defalut False, which means input is not UTC timezone (+0), and `from_timezone`
        must be given.
    from_timezone: defalut "Asia/Taipei", if is_from_utc=False, from_timezone must be given.
        if is_from_utc=True, from_timezone will be ignored.
        All timezone names can be found in pytz.all_timezones.
    is_omit_microsecond: default True, which means the microsecond part will be omitted.
    errors: {'ignore', 'raise', 'coerce'}, default 'raise'.
        - If 'raise', then invalid parsing will raise an exception.
        - If 'coerce', then invalid parsing will be set as NaT.
        - If 'ignore', then invalid parsing will return the input.

    Example
    ----------
    time_column = pd.Series(['2022/12/31 00:12:21', '2022/1/31 01:02:03'])
    convert_str_to_time_format(time_column)
    # Output:
    # 0   2022-12-31 00:12:21+08:00
    # 1   2022-01-31 01:02:03+08:00
    # dtype: datetime64[ns, Asia/Taipei]

    time_column = pd.Series(['110/12/31 00:12:21', '111/1/31 01:02:03'])
    convert_str_to_time_format(time_column, from_format='%TY/%m/%d %H:%M:%S')
    # Output:
    # 0   2021-12-31 00:12:21+08:00
    # 1   2022-01-31 01:02:03+08:00
    # dtype: datetime64[ns, Asia/Taipei]

    from numpy import nan
    time_column = pd.Series([None, nan, '', float('inf'), float('-inf'), '110/12/31T00:12:21'])
    convert_str_to_time_format(time_column, from_format='%TY/%m/%dT%H:%M:%S')
    # Output:
    # 0                         NaT
    # 1                         NaT
    # 2                         NaT
    # 3                         NaT
    # 4                         NaT
    # 5   2021-12-31 00:12:21+08:00
    # dtype: datetime64[ns, Asia/Taipei]

    time_column = pd.Series(['110/12/31 00:12:21', '111/1/31 01:02:03'])
    convert_str_to_time_format(time_column, from_format='%TY/%m/%d %H:%M:%S', is_from_utc=True)
    # Output:
    # 0   2021-12-31 08:12:21+08:00
    # 1   2022-01-31 09:02:03+08:00
    # dtype: datetime64[ns, Asia/Taipei]

    time_column = pd.Series(['110/12/31', '111/1/31'])
    date_col = convert_str_to_time_format(time_column, from_format='%TY/%m/%d', output_level='date')
    print(date_col)
    # Output
    # 0    2021-12-31
    # 1    2022-01-31
    # dtype: object
    print(type(date_col.iloc[0]))
    # Output:
    # <class 'datetime.date'>

    time_column = pd.Series(['110/12/31', '111/1/31'])
    str_datetime_col = convert_str_to_time_format(
        time_column, from_format='%TY/%m/%d', output_type='str'
    )
    print(str_datetime_col)
    # >>> print(str_datetime_col)
    # 0    2021-12-31
    # 1    2022-01-31
    # dtype: object
    print(type(str_datetime_col.iloc[0]))
    # >>> print(type(str_datetime_col.iloc[0]))
    # <class 'str'>
    """
    time_column = _convert_inf_to_nan(time_column)

    if from_format:
        time_column, from_format = _minguo_calendar_to_gregorian(
            time_column, from_format
        )

    if is_from_utc:
        time_column = pd.to_datetime(time_column, utc=True, errors=errors)
        time_column = time_column.dt.tz_convert(to_timezone)
    else:
        try:
            time_column = pd.to_datetime(time_column, utc=is_from_utc, erroe=errors)
            time_column = time_column.dt.tz_localize(from_timezone)
        except TypeError:
            # if the input is not a string, it will raise a TypeError
            # If parsing fails, convert input to string, remove timezone, and retry.
            offset_hour_str = _get_offset_hour(from_timezone)
            time_column = time_column.astype(str).str.replace(
                offset_hour_str, "", regex=False
            )
            time_column = pd.to_datetime(time_column, utc=is_from_utc, errors=errors)
            time_column = time_column.dt.tz_localize(from_timezone)

    if is_omit_microsecond:
        time_column = time_column.dt.floor("s")

    if output_level == "date":
        time_column = time_column.dt.date

    if output_type == "str":
        time_column = time_column.astype(str)

    return time_column
