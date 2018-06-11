# 数字转字符串
def change_digit_to_string(data, name='input data'):
    if isinstance(data, (int, float)):
        new_data = str(round(data))
    elif isinstance(data, str):
        new_data = data
    else:
        raise ValueError('Cannot change ['+ str(data) + '] to digit, please check ' + name)
    return new_data


# 字符串转数字
def change_string_to_digit(data, name='input data'):
    if data is None or data == '' or isinstance(data, (int, float)):
        new_data = data
    elif isinstance(data, str):
        if data.isdigit():
            new_data = float(data)
        else:
            float_data = data.split(sep='.')
            if len(float_data) == 2 and float_data[0].isdigit() and float_data[1].isdigit():
                new_data = float(data)
            else:
                raise ValueError('Cannot change ['+ str(data) + '] to digit, please check ' + name)
    else:
        raise ValueError('Cannot change ['+ str(data) + '] to digit, please check ' + name)
    return new_data


# 去掉两端的换行和空格
def remove_line_break_and_blank_from_both_ends(str_):
    str_ = str_.strip()
    while(True):
        if 1>len(str_):
            break
        if str_[0] in ('\n', '\r'):
            str_ = str_[1:].strip()
        elif str_[-1] in ('\n', '\r'):
            str_ = str_[:-1].strip()
        else:
            break
    return str_


# 去掉两端的换行
def remove_line_break_from_both_ends(str_):
    while(True):
        if 1>len(str_):
            break
        if str_[0] in ('\n', '\r'):
            str_ = str_[1:]
        elif str_[-1] in ('\n', '\r'):
            str_ = str_[:-1]
        else:
            break
    return str_