import re


# 数字转字符串
def change_digit_to_string(data, name='input data'):
    if isinstance(data, (int, float)):
        new_data = str(round(data))
    elif isinstance(data, str):
        new_data = data
    else:
        raise ValueError('Cannot change [{}] to digit, please check {}'.format(str(data), name))
    return new_data


# 字符串转数字
def convert_string_to_float(s: str, _round=None, _raise=False) -> float | None:
    # 正则表达式匹配所有合法数字格式（整数、小数、科学计数法、正负号）
    pattern = r'^[-+]?'  # 匹配正负号（可选）
    pattern += r'(?:'  # 分组开始
    pattern += r'\d+\.?\d*'  # 整数或小数（如 123, 123.45）
    pattern += r'|\.\d+'  # 纯小数（如 .45）
    pattern += r')'  # 分组结束
    pattern += r'(?:[eE][-+]?\d+)?'  # 科学计数法（如 e5, E-3）
    pattern += r'$'  # 字符串结束

    if re.fullmatch(pattern, s):
        _ = float(s)
        if _round is not None:
            _ = round(_, _round)
        return _
    else:
        if _raise:
            raise ValueError(f"Cannot change [{s}] to digit.")
        return None


# 去掉两端的换行和空格
def remove_line_break_and_blank_from_both_ends(str_):
    str_ = str_.strip()
    while True:
        if 1 > len(str_):
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
    while True:
        if 1 > len(str_):
            break
        if str_[0] in ('\n', '\r'):
            str_ = str_[1:]
        elif str_[-1] in ('\n', '\r'):
            str_ = str_[:-1]
        else:
            break
    return str_


if __name__ == '__main__':
    print(convert_string_to_float(""))
