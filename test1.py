import datetime
import time

print(datetime.datetime.fromtimestamp(1525765112.123))
print(datetime.datetime.now())
print(type(datetime.datetime.now()))
a = '2018-05-10 16:20:15'


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

print(str_to_time(a, '%Y-%m-%d %H:%M:%S'))
