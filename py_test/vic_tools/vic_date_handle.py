import datetime
import time


# 字符串转时间
def str_to_time(str_='now', time_format=''):
    str_ = str(str_).lower()
    time_ = None
    if str_ == 'now':
        time_ = datetime.datetime.now()
    elif time_format != '':
        try:
            time_ = datetime.datetime.strptime(str_, time_format)
        except ValueError:
            raise ValueError('无法转换【{}】为指定的时间格式【{}】'.format(str_, time_format))
    else:
        for time_format in (
                '%Y-%m-%d %H:%M:%S.%f', '%Y%m%d%H%M%S%f', '%Y-%m-%d %H:%M:%S', '%Y%m%d%H%M%S', '%Y-%m-%d', '%Y%m%d'):
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
    if time_format in ('', None):
        time_format = '%Y-%m-%d %H:%M:%S'
    elif time_format == 'date':
        time_format = '%Y-%m-%d'
    elif time_format == 'full':
        time_format = '%Y-%m-%d %H:%M:%S.%f'
    elif time_format in ('without_separator', 'ws'):
        time_format = '%Y%m%d%H%M%S'
    elif time_format in ('date_without_separator', 'dws'):
        time_format = '%Y%m%d'
    elif time_format in ('full_without_separator', 'fws'):
        time_format = '%Y%m%d%H%M%S%f'
    elif time_format in ('year', 'Y'):
        time_format = '%Y'
    elif time_format in ('month', 'm'):
        time_format = '%m'
    elif time_format in ('day', 'd'):
        time_format = '%d'
    elif time_format in ('hour', 'H'):
        time_format = '%H'
    elif time_format in ('minute', 'M'):
        time_format = '%M'
    elif time_format in ('second', 'S'):
        time_format = '%S'
    elif time_format in ('microsecond', 'ms', 'f'):
        time_format = '%f'
    elif time_format in ('week', 'W'):
        time_format = '%W'
    elif time_format in ('week_day', 'wd', 'w'):
        time_format = '%w'
    elif time_format in ('year_day', 'yd', 'j'):
        time_format = '%j'
    elif '%' not in time_format:
        raise ValueError('Invalid format string')
    str_ = time_.strftime(time_format)
    return str_


# 时间转时间戳
def time_to_timestamp(time_=datetime.datetime.now()):
    if time_.microsecond == 0:
        timestamp = int(time.mktime(time_.timetuple()))
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
    add_unit = str(add_unit).lower()
    if add_value in ('', None):
        add_value = 0
    if add_unit in ('year', 'Y'):
        time_ = time_ + datetime.timedelta(days=float(add_value) * 365)
    elif add_unit in ('month', 'm'):
        time_ = time_ + datetime.timedelta(days=float(add_value) * 30)
    elif add_unit in ('week', 'w'):
        time_ = time_ + datetime.timedelta(weeks=float(add_value))
    elif add_unit in ('day', 'd'):
        time_ = time_ + datetime.timedelta(days=float(add_value))
    elif add_unit in ('hour', 'H'):
        time_ = time_ + datetime.timedelta(hours=float(add_value))
    elif add_unit in ('minute', 'M'):
        time_ = time_ + datetime.timedelta(minutes=float(add_value))
    elif add_unit in ('second', 'S'):
        time_ = time_ + datetime.timedelta(seconds=float(add_value))
    else:
        raise ValueError('[' + add_unit + '] is an invalid add_unit')
    return time_
