import logging
import uuid
from random import random
from urllib.parse import quote
from py_test.general import vic_variables
from py_test.vic_tools import vic_eval, vic_date_handle


# 验证文件名称是否合法
def check_name(name, invalid_character=r'\/:*?<>|'):
    check_result = [True, name]
    if name == '':
        check_result = [False, 'Name is empty!']
    else:
        for i in invalid_character:
            if i in name:
                check_result = [False, 'Invalid name [' + name + '], contain invalid character [' + i + ']']
                break
    return check_result


# 替换字符串内的变量
def replace_parameter_in_str(
        str_, start_str, end_str, f, variables, global_variables, logger=logging.getLogger('py_test')):
    logger.debug('start replace: [%s]' % str_)
    if start_str == end_str:
        raise ValueError('start_str is same as end_str')
    while True:
        start_index = str_.find(start_str)  # 找第一个左边界
        end_index = str_.find(end_str, start_index + len(start_str))  # 找第一个左边界右边的第一个右边界
        if start_index < 0 or end_index < 0:  # 以上任意一个边界找不到则结束替换
            break
        start_index = str_.rfind(start_str, start_index, end_index)  # 找第一个左边界右边的第一个右边界的左边最近的左边界
        parameter = str_[start_index:end_index + len(end_str)].replace(start_str, '').replace(end_str, '')  # 得到需要替换的部分
        if parameter == '':
            value = ''
        else:
            value = f(parameter, variables, global_variables, logger)  # 替换
        logger.debug('%s ======> %s' % (str_[start_index:end_index + len(end_str)], value))
        # 如果返回值不是字符串且无需拼接，将直接返回替换后的对象
        if start_index == 0 and end_index + len(end_str) == len(str_) and not isinstance(value, str):
            str_ = value
            break
        else:
            str_ = str_[0:start_index] + str(value) + str_[end_index + len(end_str):]  # 为防止替换了相同的内容，采用拼接的方法
    logger.debug('end replace: [%s]' % str_)
    return str_


# 整合参数方便调用
def replace_special_value(str_, variables=None, global_variables=None, logger=logging.getLogger('py_test')):
    str_ = replace_parameter_in_str(
        str_=str_, start_str='${', end_str='}$', f=select_func, variables=variables, global_variables=global_variables,
        logger=logger)
    return str_


# 通过操作符选择变量处理方式
def select_func(str_, variables, global_variables, logger=logging.getLogger('py_test')):
    if '|' not in str_:
        value = vic_variables.get_str(str_, variables, global_variables)
    else:
        new_str = str_.split(sep='|', maxsplit=1)
        f = new_str[0]
        parameter = new_str[1]
        try:
            if f == 'r':
                value = get_random_func(parameter)
            elif f == 't':
                value = get_time_str_func(parameter)
            elif f == 'ts':
                value = get_timestamp_str_func(parameter)
            elif f == 'tst':
                value = timestamp_to_time_str_func(parameter)
            elif f == 'url':
                value = encode_url_func(parameter)
            elif f == 'cal':
                eo = vic_eval.EvalObject(
                    parameter, vic_variables.get_variable_dict(variables, global_variables), logger)
                success, eval_result, final_expression = eo.get_eval_result()
                if success:
                    value = str(eval_result)
                else:
                    value = 'Calculate Error!\nExpression:\n' + final_expression + '\n' + str(eval_result)
            elif f == 'uuid':
                value = get_uuid()
            elif f == 'slice':
                value = get_slice(parameter)
            elif f == 'int':
                try:
                    value = int(parameter)
                except ValueError:
                    raise ValueError('无法把{}转换为整型，请检查数据'.format(parameter))
            elif f == 'float':
                try:
                    value = float(parameter)
                except ValueError:
                    raise ValueError('无法把{}转换为浮点型，请检查数据'.format(parameter))
            elif f == 'bool':
                if parameter.lower() == 'false':
                    value = False
                else:
                    try:
                        value = bool(parameter)
                    except ValueError:
                        raise ValueError('无法把{}转换为布尔型，请检查数据'.format(parameter))
            elif f in ('time', 'datetime'):
                try:
                    value = get_time_func(parameter)
                except ValueError:
                    raise ValueError('无法把{}转换为时间类型，请检查数据'.format(parameter))
            else:
                raise ValueError('[' + f + '] is an invalid functions code')
        except ValueError as e:
            msg = getattr(e, 'msg', str(e))
            raise ValueError('通过操作符【{}】转换数据时出现错误，错误原因为:{}'.format(f, msg))
    return value


# 获取随机数
def get_random_value(start=0, end=1, decimal=0):
    start = float(start)
    end = float(end)
    decimal = round(float(decimal))
    value = round(start + random() * (end - start), decimal)
    if decimal == 0:
        value = int(value)
    return value


# 逗号分割的参数1代表随机数范围是从0到参数1的值，分割后的参数1，参数2代表范围，参数3代表保留的小数位
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
    return str(value)


# 分割后的参数2代表时间格式，参数3代表时间位移单位，参数4代表时间位移量
def get_time_func(str_):
    str_list = str_.split(sep=',')
    if len(str_list) == 1:
        time_ = vic_date_handle.str_to_time(str_)
    # 参数3和4必须同时出现，只有参数3时忽略参数3
    elif len(str_list) < 4:
        time_ = vic_date_handle.str_to_time(str_list[0], str_list[1])
    else:
        time_ = vic_date_handle.str_to_time(str_list[0], str_list[1])
        time_ = vic_date_handle.time_add(time_, str_list[2], str_list[3])
    return time_


# 逗号分割的参数1代表要转换的时间，参数2代表输入时间格式，参数3代表时间位移单位，参数4代表时间位移量，参数5代表输出时间格式
def get_time_str_func(str_):
    time_ = get_time_func(str_)
    time_format = ''
    str_list = str_.split(sep=',')
    if len(str_list) == 5:
        time_format = str_list[4]
    value = vic_date_handle.time_to_str(time_, time_format)
    return value


# 逗号分割的参数1代表要转换的时间，参数2代表输入时间格式，参数3代表时间位移单位，参数4代表时间位移量，参数5代表保留的小数位数，参数6代表是否保留小数点
def get_timestamp_str_func(str_):
    time_ = get_time_func(str_)
    timestamp = vic_date_handle.time_to_timestamp(time_)
    str_list = str_.split(sep=',')
    if len(str_list) < 5:
        value = '{:.0f}'.format(timestamp)
    else:
        decimals = str_list[4] or '0'
        try:
            decimals = str(int(decimals))
            s = '%.' + decimals + 'f'
        except ValueError:
            raise ValueError('小数点位数参数【{}】必须为数字'.format(str_list[4]))
        value = s % timestamp
        if len(str_list) > 5:
            value = (s % timestamp).replace('.', '')
    return value


# 逗号分割的参数1代表要转化的时间戳，参数2代表输出的时间格式
def timestamp_to_time_str_func(str_):
    str_list = str_.split(sep=',')
    try:
        timestamp = float(str_list[0])
    except ValueError:
        raise ValueError('时间戳【{}】格式错误'.format(str_list[0]))
    time_ = vic_date_handle.timestamp_to_time(timestamp)
    if len(str_list) == 1:
        if time_.microsecond == 0:
            value = vic_date_handle.time_to_str(time_)
        else:
            value = vic_date_handle.time_to_str(time_, 'full')
    else:
        value = vic_date_handle.time_to_str(time_, str_list[1])
    return value


# 获取UUID
def get_uuid():
    return str(uuid.uuid1())


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
