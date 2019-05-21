import datetime
import time
import calendar


# 字符串转时间
def str_to_time(str_='now', time_format=''):
    str_ = str(str_)
    time_ = None
    if str_.lower() == 'now':
        time_ = datetime.datetime.now()
    elif time_format != '':
        try:
            time_ = datetime.datetime.strptime(str_, time_format)
        except ValueError:
            raise ValueError('无法转换【{}】为指定的时间格式【{}】'.format(str_, time_format))
    else:
        # 尝试使用常用格式进行转换
        for time_format in (
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y.%m.%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
                '%Y.%m.%d %H:%M:%S',
                '%Y-%m-%d',
                '%Y.%m.%d',
        ):
            try:
                time_ = datetime.datetime.strptime(str_, time_format)
                break
            except ValueError:
                pass
        if time_ is None:
            raise ValueError('无法转换【{}】为常用的时间格式，请手动指定时间格式'.format(str_))
    return time_


# 时间转字符串
def time_to_str(time_=datetime.datetime.now(), time_format=''):
    try:
        time_format_ = time_format.strip()
        if time_format_ in ('', None):
            time_format = '%Y-%m-%d %H:%M:%S'
        elif time_format_ == 'date':
            time_format = '%Y-%m-%d'
        elif time_format_ == 'full':
            time_format = '%Y-%m-%d %H:%M:%S.%f'
        elif time_format_ in ('without_separator', 'ws'):
            time_format = '%Y%m%d%H%M%S'
        elif time_format_ in ('date_without_separator', 'dws'):
            time_format = '%Y%m%d'
        elif time_format_ in ('full_without_separator', 'fws'):
            time_format = '%Y%m%d%H%M%S%f'
        elif time_format_ in ('year', 'Y'):
            time_format = '%Y'
        elif time_format_ in ('month', 'm'):
            time_format = '%m'
        elif time_format_ in ('day', 'd'):
            time_format = '%d'
        elif time_format_ in ('hour', 'H'):
            time_format = '%H'
        elif time_format_ in ('minute', 'M'):
            time_format = '%M'
        elif time_format_ in ('second', 'S'):
            time_format = '%S'
        elif time_format_ in ('microsecond', 'f'):
            time_format = '%f'
        elif time_format_ == 'week':
            time_format = '%U'
        elif time_format_ in ('week_day', 'wd'):
            time_format = '%w'
        elif time_format_ in ('year_day', 'yd'):
            time_format = '%j'
        elif '%' not in time_format:
            raise ValueError
        str_ = time_.strftime(time_format)
    except ValueError:
        raise ValueError('无效的时间格式【{}】'.format(time_format))
    return str_


# 时间转时间戳
def time_to_timestamp(time_=datetime.datetime.now()):
    if time_.microsecond == 0:
        try:
            timestamp = int(time.mktime(time_.timetuple()))
        except OverflowError:
            raise ValueError('时间戳超过允许的范围（1970-01-01 8:00:00到3001-01-01 15:59:59）')
    else:
        microsecond = time_.microsecond / 1000000
        timestamp = time.mktime(time_.timetuple()) + microsecond
    return timestamp


# 时间戳转时间
def timestamp_to_time(timestamp=time.time()):
    time_ = datetime.datetime.fromtimestamp(timestamp)
    return time_


# 时间偏移
def time_add(time_=datetime.datetime.now(), add_unit='d', add_value=0):
    if add_unit in ('', None):
        add_unit = 'd'
    if add_value in ('', None):
        add_value = 0
    if add_unit in ('year', 'Y'):
        # time_ = time_ + datetime.timedelta(days=float(add_value) * 365)
        time_ = delta_month(time_, 12*round(float(add_value)))
    elif add_unit in ('month', 'm'):
        # time_ = time_ + datetime.timedelta(days=float(add_value) * 30)
        time_ = delta_month(time_, round(float(add_value)))
    elif add_unit in ('day', 'd'):
        time_ = time_ + datetime.timedelta(days=float(add_value))
    elif add_unit in ('hour', 'H'):
        time_ = time_ + datetime.timedelta(hours=float(add_value))
    elif add_unit in ('minute', 'M'):
        time_ = time_ + datetime.timedelta(minutes=float(add_value))
    elif add_unit in ('second', 'S'):
        time_ = time_ + datetime.timedelta(seconds=float(add_value))
    elif add_unit in ('microsecond', 'f'):
        time_ = time_ + datetime.timedelta(microseconds=float(add_value))
    elif add_unit in ('week', 'w'):
        time_ = time_ + datetime.timedelta(weeks=float(add_value))
    else:
        raise ValueError('无效的时间偏移单位【{}】'.format(add_unit))
    return time_


# timedelta转人性化字符串
def get_timedelta_str(timedelta_, ndigits=0):
    remain_seconds = abs(timedelta_.total_seconds())
    days = int(remain_seconds / 24 / 3600)
    remain_seconds = remain_seconds - days * 24 * 3600
    hours = int(remain_seconds / 3600)
    remain_seconds = remain_seconds - hours * 3600
    minutes = int(remain_seconds / 60)
    remain_seconds = remain_seconds - minutes * 60
    seconds = round(remain_seconds, ndigits)

    if ndigits == 0:
        seconds = int(seconds)

    str_ = '0秒'
    if days > 0:
        str_ = '{}天{}小时{}分{}秒'.format(days, hours, minutes, seconds)
    elif hours > 0:
        str_ = '{}小时{}分{}秒'.format(hours, minutes, seconds)
    elif minutes > 0:
        str_ = '{}分{}秒'.format(minutes, seconds)
    elif seconds > 0:
        str_ = '{}秒'.format(seconds)

    if timedelta_.total_seconds() < 0 < seconds:
        str_ = '负{}'.format(str_)

    return str_


# 按月份偏移，如果偏移后日期大于那个月份的最大日期，将取最大日期
def delta_month(date, add_month):
    month_dict = (12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

    month = date.month + add_month
    new_month = month_dict[month % 12]
    new_year = date.year + month // 12
    if new_month == 12:
        new_year -= 1
    new_day = date.day
    max_day = calendar.monthrange(new_year, new_month)[1]  # 获取新日期月份的最后一天
    new_day = max_day if max_day < new_day else new_day
    return datetime.datetime(
        new_year, new_month, new_day, date.hour, date.minute, date.second, date.microsecond, date.tzinfo)
