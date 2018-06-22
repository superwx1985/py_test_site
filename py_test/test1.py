from py_test.vic_tools.vic_date_handle import *

a = str_to_time('2018-06-11 11:11:11.510000')
b = str_to_time('2018-06-11 11:11:12')

print(a)
print(b)

c = a - b

print(c)
print(c.total_seconds())



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


print(get_timedelta_str(c))
