import uuid
from random import random
from urllib.parse import quote
from py_test.vic_tools.vic_date_handle import *


# 获取随机数
def get_random_value(start=0, end=1, decimal=0):
    start = float(start)
    end = float(end)
    decimal = round(float(decimal))
    value = round(start + random() * (end - start), decimal)
    if decimal == 0:
        value = int(value)
    return value


# 分割前的参数1代表随机数范围是从0到参数1的值，分割后的参数1，参数2代表范围，参数3代表保留的小数位
def get_random_func(str_):
    if str_.find(',') == -1:
        value = get_random_value(0, str_)
    else:
        str_list = str_.split(sep=',')
        if len(str_list) == 3:
            value = get_random_value(str_list[0], str_list[1], str_list[2])
        elif len(str_list) == 2:
            value = get_random_value(str_list[0], str_list[1])
        else:
            raise ValueError('[' + str_ + '] is an invalid for get_random_func function')
    return value


# 分割后的参数2代表时间格式，参数3代表时间位移单位，参数4代表时间位移量
def get_time_func(str_):
    if str_.find(',') == -1:
        time_ = str_to_time(str_)
        value = time_to_str(time_)
    else:
        str_list = str_.split(sep=',')
        if len(str_list) == 4:
            time_ = str_to_time(str_list[0])
            time_ = time_add(time_, str_list[2], str_list[3])
            value = time_to_str(time_, str_list[1])
        elif len(str_list) == 2 or len(str_list) == 3:
            time_ = str_to_time(str_list[0])
            value = time_to_str(time_, str_list[1])
        else:
            raise ValueError('[' + str_ + '] is an invalid parameter for get_time_func function')
    return value


# 分割后的参数2代表保留的小数位数，参数3代表是否保留小数点，返回精确到毫秒的时间戳
def get_timestamp_func(str_):
    if str_.find(',') == -1:
        time_ = str_to_time(str_)
        timestamp = time_to_timestamp(time_)
        value = '%.3f' % timestamp
    else:
        str_list = str_.split(sep=',')
        time_ = str_to_time(str_list[0])
        timestamp = time_to_timestamp(time_)
        try:
            from py_test.vic_tools.vic_str_handle import change_string_to_digit
            decimals = str(int(change_string_to_digit(str_list[1])))
            s = '%.' + decimals + 'f'
        except ValueError:
            raise ValueError('[' + str_ + '] is an invalid parameter for get_timestamp_func function')
        if len(str_list) == 2:
            value = s % timestamp
        else:
            value = (s % timestamp).replace('.', '')
    return value


# 分割后的参数2代表取出的时间格式
def timestamp_to_time_func(str_):
    if str_.find(',') == -1:
        time_ = timestamp_to_time(float(str_))
        if time_.microsecond == 0:
            value = time_to_str(time_)
        else:
            value = time_to_str(time_, 'full')
    else:
        str_list = str_.split(sep=',')
        if len(str_list) == 2:
            time_ = timestamp_to_time(float(str_list[0]))
            value = time_to_str(time_, str_list[1])
        else:
            raise ValueError('[' + str_ + '] is an invalid parameter for timestamp_to_time_func function')
    return value


# 获取UUID
def get_uuid():
    return uuid.uuid1()


# 切片操作
def get_slice(str_):
    str_list = str_.split(sep=',')

    try:
        if len(str_list) == 1:
            new_str = str_
        elif len(str_list) == 2:
            index_ = int(str_list[1])
            new_str = str_list[0][index_]
        elif len(str_list) == 3:
            start_index = ''
            end_index = ''
            if str_list[1].strip() != '':
                start_index = int(str_list[1])
            if str_list[2].strip() != '':
                end_index = int(str_list[2])
            if isinstance(start_index, int) and isinstance(end_index, int):
                new_str = str_list[0][start_index:end_index]
            elif isinstance(start_index, int):
                new_str = str_list[0][start_index:]
            elif isinstance(end_index, int):
                new_str = str_list[0][:end_index]
            else:
                new_str = str_list[0]
        elif len(str_list) == 4:
            start_index = ''
            end_index = ''
            step = ''
            if str_list[1].strip() != '':
                start_index = int(str_list[1])
            if str_list[2].strip() != '':
                end_index = int(str_list[2])
            if str_list[3].strip() != '':
                step = int(str_list[3])
            if isinstance(start_index, int) and isinstance(end_index, int) and isinstance(step, int):
                new_str = str_list[0][start_index:end_index:step]
            elif isinstance(start_index, int) and isinstance(end_index, int):
                new_str = str_list[0][start_index:end_index:]
            elif isinstance(start_index, int) and isinstance(step, int):
                new_str = str_list[0][start_index::step]
            elif isinstance(end_index, int) and isinstance(step, int):
                new_str = str_list[0][:end_index:step]
            elif isinstance(start_index, int):
                new_str = str_list[0][start_index::]
            elif isinstance(end_index, int):
                new_str = str_list[0][:end_index:]
            elif isinstance(step, int):
                new_str = str_list[0][::step]
            else:
                new_str = str_list[0]
        else:
            raise ValueError
    except ValueError or IndexError:
        raise ValueError('slice操作符接收到一个非法的参数【{}】，请检查'.format(str_))
    return new_str


# 转换为URL编码
def encode_url_func(str_):
    try:
        value = quote(str_)
    except Exception as e:
        raise ValueError('Cannot encode [' + str_ + ']. ' + str(e))
    return value
