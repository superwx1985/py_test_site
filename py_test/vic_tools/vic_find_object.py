import json
import re
import uuid
import logging
from copy import deepcopy
from py_test.vic_tools import vic_eval
from py_test.vic_tools.vic_date_handle import str_to_time
from py_test.vic_tools.attr_display import AttrDisplay
from py_test.vic_tools.vic_str_handle import remove_line_break_and_blank_from_both_ends, remove_line_break_from_both_ends


# 在对象中查找对象
class FindObject:
    def __init__(self, list_exact_match=False, dict_exact_match=False, default_operator_list=None,
                 logger=logging.getLogger('py_test')):
        # 如果__list_exact_match设为True，则两个列表的值顺序及数量都一致才能标记为found，否则只需要目标列表包含期望列表（无序）
        self.__list_exact_match = list_exact_match
        # 如果__dict_exact_match设为True，则两个字典的key，value一一对应才能标记为found，否则只需要目标字典包含期望字典
        self.__dict_exact_match = dict_exact_match
        self.default_operator_list = default_operator_list
        self.logger = logger

    # 主方法，object1为期望对象，object2为目标对象
    def find_object_in_object(self, object1, object2):
        found = False
        count = 0
        re_result = list()
        error_msg = None

        # self.logger.debug('object1: %s' % object1)
        # self.logger.debug('object2: %s' % object2)

        # 如果对象相等
        # if object1 == object2:
        #     found = True
        #     count += 1
        #     return found, count, re_result

        # 判断对象类型是否一致，如果一致就调用对应的比较方法获取比较结果
        _found = False
        _re_result = None
        _error_msg = None
        if isinstance(object1, (list, tuple)) and isinstance(object2, type(object1)):
            _found, _count, _re_result, _error_msg = self.find_list1_in_list2(object1, object2)
        elif isinstance(object1, dict) and isinstance(object2, type(object1)):
            _found, _count, _re_result, _error_msg = self.find_dict1_in_dict2(object1, object2)

        if _found:
            found = True
            count += 1
            if isinstance(_re_result, list):
                re_result.extend(_re_result)
        elif _error_msg:
            error_msg = _error_msg

        # 判断object2是否是可迭代的对象，如果是，则拆分该对象，递归调用本方法继续比较
        if isinstance(object2, (list, tuple)):
            for v in object2:
                if isinstance(v, (list, tuple, dict)):
                    _found, _count, _re_result, _error_msg = self.find_object_in_object(object1, v)
                    if _found:
                        found = True
                        count += _count
                        if isinstance(_re_result, list):
                            re_result.extend(_re_result)
                    elif _error_msg:
                        error_msg = _error_msg
        elif isinstance(object2, dict):
            for v in object2.values():
                if isinstance(v, (list, tuple, dict)):
                    _found, _count, _re_result, _error_msg = self.find_object_in_object(object1, v)
                    if _found:
                        found = True
                        count += _count
                        if isinstance(_re_result, list):
                            re_result.extend(_re_result)
                    elif _error_msg:
                        error_msg = _error_msg

        # self.logger.debug('found: %s count: %s' % (found, count))
        # self.logger.debug('object:\n%s' % object2)
        return found, count, re_result, error_msg

    # 在列表和元组中查找列表和元组
    def find_list1_in_list2(self, list1, list2):
        found = False
        count = 0
        re_result = list()
        error_msg = None
        # list1及list2长度均为0，返回found为True
        if 0 == len(list1) and 0 == len(list2):
            found = True
            count = 1
            return found, count, re_result, error_msg
        # 如果__list_exact_match设为True，则两个列表的值顺序及数量都一致才能标记为found
        elif self.__list_exact_match:
            # 如果list1和list2长度不一致，直接返回found为False
            if len(list1) != len(list2):
                return found, count, re_result, error_msg
            i = -1
            for v in list1:
                i += 1
                # 如果list1和list2相同索引的值为tuple或list，调用find_list1_in_list2
                if isinstance(v, (tuple, list)) and isinstance(list2[i], type(v)):
                    _found, _count, _re_result, _error_msg = self.find_list1_in_list2(v, list2[i])
                    if _found:
                        count += 1
                        if isinstance(_re_result, list):
                            re_result.extend(_re_result)
                    elif _error_msg:
                        error_msg = _error_msg
                # 如果list1和list2相同索引的值为dict，调用find_dict1_in_dict2
                elif isinstance(v, dict) and isinstance(list2[i], type(v)):
                    _found, _count, _re_result, _error_msg = self.find_dict1_in_dict2(v, list2[i])
                    if _found:
                        count += 1
                        if isinstance(_re_result, list):
                            re_result.extend(_re_result)
                    elif _error_msg:
                        error_msg = _error_msg
                # 如果v为str，调用find_with_condition方法进行比较
                elif isinstance(v, str):
                    find_result = find_with_condition(
                        v, list2[i], default_operator_list=self.default_operator_list, logger=self.logger,)
                    if find_result.is_matched:
                        count += 1
                        if isinstance(find_result.re_result, list):
                            re_result.extend(find_result.re_result)
                    elif find_result.error_msg:
                        error_msg = find_result.error_msg
                elif v == list2[i]:
                    count += 1
            # 如果匹配数和list1长度一致，则标记为found
            if count == len(list1):
                found = True
        # 如果__list_exact_match不为True，则list1的值存在于list2中，即可标记为found
        else:
            # 如果list1的长度大于list的长度，返回found为False
            if len(list1) > len(list2):
                return found, count, re_result, error_msg
            list2_original = deepcopy(list2)  # 防止remove影响到pre_data_object
            for v1 in list1:
                list2_temp = deepcopy(list2_original)
                for v2 in list2_temp:
                    # 如果v1和v2为tuple或list，调用find_list1_in_list2
                    if isinstance(v1, (tuple, list)) and isinstance(v2, type(v1)):
                        _found, _count, _re_result, _error_msg = self.find_list1_in_list2(v1, v2)
                        if _found:
                            count += 1
                            list2_original.remove(v2)
                            if isinstance(_re_result, list):
                                re_result.extend(_re_result)
                            break
                        elif _error_msg:
                            error_msg = _error_msg
                    # 如果v1和v2为dict，调用find_dict1_in_dict2
                    elif isinstance(v1, dict) and isinstance(v2, type(v1)):
                        _found, _count, _re_result, _error_msg = self.find_dict1_in_dict2(v1, v2)
                        if _found:
                            count += 1
                            list2_original.remove(v2)
                            if isinstance(_re_result, list):
                                re_result.extend(_re_result)
                            break
                        elif _error_msg:
                            error_msg = _error_msg
                    # 如果v1为str，调用find_with_condition方法进行比较
                    elif isinstance(v1, str):
                        find_result = find_with_condition(
                            v1, v2, default_operator_list=self.default_operator_list, logger=self.logger)
                        if find_result.is_matched:
                            count += 1
                            list2_original.remove(v2)
                            if isinstance(find_result.re_result, list):
                                re_result.extend(find_result.re_result)
                            break
                        elif find_result.error_msg:
                            error_msg = find_result.error_msg
                    elif v1 == v2:
                        count += 1
                        list2_original.remove(v2)
                        break
            # 如果匹配数和list1长度一致，则标记为found
            if count == len(list1):
                found = True
        return found, count, re_result, error_msg

    # 在字典中查找字典
    def find_dict1_in_dict2(self, dict1, dict2):
        found = False
        count = 0
        re_result = list()
        error_msg = None
        for k, v in dict1.items():
            # 如果在dict2中无对应的key，跳过当次匹配
            if k not in dict2:
                continue
            # 如果dict1和dict2相同key对应的值为tuple或list，调用find_list1_in_list2
            if isinstance(v, (tuple, list)) and isinstance(dict2[k], type(v)):
                _found, _count, _re_result, _error_msg = self.find_list1_in_list2(v, dict2[k])
                if _found:
                    count += 1
                    if isinstance(_re_result, list):
                        re_result.extend(_re_result)
                elif _error_msg:
                    error_msg = _error_msg
            # 如果dict1和dict2相同key对应的值为dict，调用find_dict1_in_dict2
            elif isinstance(v, dict) and isinstance(dict2[k], type(v)):
                _found, _count, _re_result, _error_msg = self.find_dict1_in_dict2(v, dict2[k])
                if _found:
                    count += 1
                    if isinstance(_re_result, list):
                        re_result.extend(_re_result)
                elif _error_msg:
                    error_msg = _error_msg
            # 如果v为str，调用find_with_condition方法进行比较
            elif isinstance(v, str):
                find_result = find_with_condition(
                    v, dict2[k], default_operator_list=self.default_operator_list, logger=self.logger)
                if find_result.is_matched:
                    count += 1
                    if isinstance(find_result.re_result, list):
                        re_result.extend(find_result.re_result)
                elif find_result.error_msg:
                    error_msg = find_result.error_msg
            elif v == dict2[k]:
                count += 1
        # 如果匹配数和dict1长度一致，则标记为found
        if count == len(dict1):
            found = True
        # 如果__dict_exact_match设为True，则两个字典的key，value一一对应才能标记为found
        if self.__dict_exact_match:
            if count < len(dict2):
                found = False
        return found, count, re_result, error_msg


# 保存查找结果
class FindResult(AttrDisplay):
    def __init__(
            self, is_matched, condition, data, match_count, condition_value, operator_list, data_object,
            re_result=None, error_msg=''):
        self.is_matched = is_matched
        self.condition = condition
        self.data = data
        self.match_count = match_count
        self.condition_value = condition_value
        self.operator_list = operator_list
        self.data_object = data_object
        self.re_result = re_result
        self.error_msg = error_msg


# 根据参数生成正则表达式flags的值
def generate_reg_flags(re_parameter):
    re_parameter_list = list(re_parameter)
    re_ = {
        'I': re.I,  # 使匹配对大小写不敏感
        'L': re.L,  # 做本地化识别（locale-aware）匹配
        'M': re.M,  # 多行匹配，影响^和$
        'S': re.S,  # 使.匹配包括换行在内的所有字符
        'U': re.U,  # 根据Unicode字符集解析字符。这个标志影响 \w, \W, \b, \B
        'X': re.X,  # 给予更灵活的格式以便将正则表达式写得更易于理解
    }
    flags = 0
    for flag in re_parameter_list:
        try:
            flags = flags | re_[flag.upper()]
        except KeyError:
            raise ValueError('Invalid reg flag [%s]' % flag)
    return flags


# 提取re_result中的文本
def get_first_text_in_re_result(re_result):
    text = None
    if isinstance(re_result, list):
        for l in re_result:
            if isinstance(l, str):
                text = l
                break
            elif isinstance(l, tuple):
                for t in l:
                    if isinstance(t, str) and t != '':
                        text = t
                        break
                if text:
                    break
    return text


# 替换成对标识里面的特殊字符，参数f为自定义替换函数，接收成对标识之间的字符串，返回替换后的字符串
def replace_control_character(str_, f, start_str, end_str):
    # logger = get_thread_logger()
    # logger.debug('start replace: [%s]' % str_)
    start_str_temp = '{L_%s}' % str(uuid.uuid1())
    end_str_temp = '{R_%s}' % str(uuid.uuid1())

    while True:
        start_index = str_.find(start_str)  # 找第一个左边界
        end_index = str_.find(end_str, start_index + len(start_str))  # 找第一个左边界右边的第一个右边界
        if start_index < 0 or end_index < 0:  # 以上任意一个边界找不到则结束替换
            break
        str_ = str_[0:end_index] + end_str_temp + str_[end_index + len(end_str):]
        start_index = str_.rfind(start_str, start_index, end_index)  # 找第一个左边界右边的第一个右边界的左边最近的左边界
        str_ = str_[0:start_index] + start_str_temp + str_[start_index + len(start_str):]
        end_index = end_index + (len(start_str_temp) - len(start_str))
        original_value = str_[start_index + len(start_str_temp):end_index]  # 得到需要替换的部分
        if original_value == '':
            replaced_value = ''
        else:
            replaced_value = str(f(original_value))  # 替换
        # logger.debug('%s => %s' % (original_value, replaced_value))
        str_ = str_[0:start_index + len(start_str_temp)] + replaced_value + str_[end_index:]  # 为防止替换了相同的内容，采用拼接的方法
    str_ = str_.replace(start_str_temp, start_str).replace(end_str_temp, end_str)
    # logger.debug('end replace: [%s]' % str_)
    return str_


# 替换json字符串中字符串值里的特殊符号
def replace_control_character_in_json(json_):
    return json_.replace("\b", "#{$b}#").replace("\t", "#{$t}#").replace("\n", "#{$n}#").replace(
        "\f", "#{$f}#").replace("\r", "#{$r}#").replace("\a", "#{$a}#").replace("\\", "#{$}#")


def get_python_vaild_json(json_):
    json_ = json_.replace('\\"', '#{$dq}#')  # 把转义的双引号暂时替换为其他符号，防止循环替换时被找到
    json_ = replace_control_character(json_, replace_control_character_in_json, '"', '"')
    json_ = json_.replace("\b", "").replace("\t", "").replace("\n", "").replace("\f", "").replace("\r", "").replace(
        "\a", "")
    json_ = json_.replace('#{$dq}#', '\\"')  # 把转义的双引号替换回来
    return json_


# 还原字符串中被替换的特殊符号
def restore_control_character(str_):
    return str_.replace("#{$b}#", "\b").replace("#{$t}#", "\t").replace("#{$n}#", "\n").replace("#{$f}#", "\f").replace(
        "#{$r}#", "\r").replace("#{$a}#", "\a").replace("#{$}#", "\\")


# 还原字典中被替换的特殊符号
def restore_control_character_in_dict(dict_, f):
    dict_new = dict()
    for k, v in dict_.items():
        if str == type(k):
            k = f(k)
        elif dict == type(k):
            k = restore_control_character_in_dict(k, f)
        elif list == type(k):
            k = restore_control_character_in_list(k, f)
        if str == type(v):
            v = f(v)
        elif dict == type(v):
            v = restore_control_character_in_dict(v, f)
        elif list == type(v):
            v = restore_control_character_in_list(v, f)
        dict_new[k] = v
    return dict_new


# 还原列表中被替换的特殊符号
def restore_control_character_in_list(list_, f):
    list_new = list()
    for v in list_:
        if str == type(v):
            v = f(v)
        elif dict == type(v):
            v = restore_control_character_in_dict(v, f)
        elif list == type(v):
            v = restore_control_character_in_list(v, f)
        list_new.append(v)
    return list_new


# 还原对象中被替换的特殊符号
def restore_control_character_in_objecr(object_, f):
    if dict == type(object_):
        return restore_control_character_in_dict(object_, f)
    elif list == type(object_):
        return restore_control_character_in_list(object_, f)


# 分解操作符
def resolve_operator(condition, start_str='#{', end_str='}#', default_operator_list=None):
    operator_character = ''
    start_index = condition.find(start_str)  # 找第一个左边界
    end_index = condition.find(end_str, start_index + len(start_str))  # 找第一个左边界右边的第一个右边界
    if start_index < 0 or end_index < 0:  # 以上任意一个边界找不到则结束替换
        condition_value = condition
    else:
        start_index = condition.rfind(start_str, start_index, end_index)  # 找第一个左边界右边的第一个右边界的左边最近的左边界
        operator_character = condition[start_index:end_index + len(end_str)]
        condition_value = condition[0:start_index] + condition[end_index + len(end_str):]

    # logger.debug('operator_character:\n%s' % operator_character)
    # logger.debug('condition_value:\n%s' % condition_value)
    # logger.debug('data:\n%s' % data)

    operator_list = operator_character.replace(start_str, '').replace(end_str, '').split(sep='|')
    first_operator = ''
    if operator_list:
        first_operator = operator_list[0].replace('\r', '').replace('\n', '').strip().lower()
    if first_operator == '' and isinstance(default_operator_list, list) and default_operator_list:
        operator_list = default_operator_list
        first_operator = operator_list[0].replace('\r', '').replace('\n', '').strip().lower()
    return operator_character, condition_value, operator_list, first_operator


# 按条件查找
def find_with_condition(
        condition, data, pre_data_object=None, default_operator_list=None, logger=logging.getLogger('py_test')):
    """
    在data中查找满足condition的内容，condition可包含操作符
    pre_data_object 用于传入一个已处理好的tuple，list，dict，以免data被多次转换影响性能
    default_operator_list 用于传入一个默认的操作符列表，如果condition不包含任何操作符，将使用默认操作符列表
    """
    is_matched = False
    match_count = -1
    condition_value = ''
    operator_list = ''
    data_object = None
    re_result = None
    error_msg = None

    try:
        operator_character, condition_value, operator_list, first_operator = resolve_operator(
            condition, default_operator_list=default_operator_list)

        # 处理无操作符的条件
        if first_operator == '':
            if condition_value == '':
                if str(data) == '':
                    match_count = 1
                else:
                    match_count = 0
            else:
                match_count = str(data).count(condition_value)
            if match_count > 0:
                is_matched = True

        # 处理有操作符的条件
        else:
            parameter_list = []
            if len(operator_list) > 1:
                parameter_list = operator_list[1].split(sep=',')  # 这里故意不去掉参数两端的空格及换行，有些参数需要保留这些内容

            # 处理数量匹配
            if first_operator == 'count':
                find_result_temp = find_with_condition(condition_value, data, logger=logger)
                if find_result_temp.is_matched:
                    # 出现1次及以上
                    if len(parameter_list) == 0 or parameter_list[0] in ('+', 'n'):
                        if find_result_temp.match_count > 0:
                            is_matched = True
                    else:
                        try:
                            count_int = int(parameter_list[0])
                            if find_result_temp.match_count == count_int:
                                is_matched = True
                        except ValueError:
                            eo = vic_eval.EvalObject(parameter_list[0], {'x': find_result_temp.match_count}, logger)
                            eval_success, eval_result, final_expression = eo.get_eval_result()
                            if eval_success:
                                if eval_result:
                                    is_matched = True
                            else:
                                raise ValueError('操作符【{}】处理过程中出现错误，无效的表达式【{}】'.format(
                                    operator_character, parameter_list[0]))
                operator_list.extend(find_result_temp.operator_list)
                match_count = find_result_temp.match_count
                condition_value = find_result_temp.condition_value
                data_object = find_result_temp.data_object

            # 完全相等
            elif first_operator in ('===', '!=='):
                match_count = 0
                if len(parameter_list) == 0 or parameter_list[0] == 'str':
                    pass
                elif parameter_list[0] == 'int':
                    try:
                        condition_value = int(condition_value)
                    except ValueError:
                        raise ValueError('操作符【{}】处理过程中出现错误，【{}】无法转换为整型'.format(operator_character, condition_value))
                elif parameter_list[0] == 'float':
                    try:
                        condition_value = float(condition_value)
                    except ValueError:
                        raise ValueError('操作符【{}】处理过程中出现错误，【{}】无法转换为浮点型'.format(operator_character, condition_value))
                elif parameter_list[0] in ('datetime', 'time'):
                    time_format = ''
                    if len(parameter_list) > 1:
                        time_format = parameter_list[1]
                    try:
                        condition_value = str_to_time(condition_value, time_format)
                    except ValueError:
                        raise ValueError('操作符【{}】处理过程中出现错误，【{}】无法转换为datetime类型'.format(operator_character, condition_value))
                else:
                    raise ValueError('操作符【{}】处理过程中出现错误，无效的转换类型【{}】'.format(operator_character, parameter_list[0]))
                if condition_value == data and type(condition_value) == type(data):  # 使用type()比较的方式确保类型完全相等而不单是属于子类
                    if first_operator == '===':
                        is_matched = True
                        match_count = 1
                else:
                    if first_operator == '!==':
                        is_matched = True
                        match_count = 0

            # 尝试转换为相同类型的对象再进行比较
            elif first_operator in ('==', '!=', '<=', '>=', '<', '>'):
                match_count = 0
                if len(parameter_list) == 0 or parameter_list[0] == 'str':
                    data_object = str(data)
                elif parameter_list[0] == 'int':
                    try:
                        condition_value = int(condition_value)
                    except ValueError:
                        raise ValueError('操作符【{}】处理过程中出现错误，【{}】无法转换为整型'.format(operator_character, condition_value))
                    try:
                        data_object = int(data)
                    except ValueError:
                        data_object = ValueError('Cannot change [%s] to int object' % data)
                        # raise ValueError('Cannot change [%s] to int object'%(data))
                elif parameter_list[0] == 'float':
                    try:
                        condition_value = float(condition_value)
                    except ValueError:
                        raise ValueError('操作符【{}】处理过程中出现错误，【{}】无法转换为浮点型'.format(operator_character, condition_value))
                    try:
                        data_object = float(data)
                    except ValueError:
                        data_object = ValueError('Cannot change [%s] to float object' % data)
                        # raise ValueError('Cannot change [%s] to float object'%(data))
                elif parameter_list[0] in ('datetime', 'time'):
                    time_format = ''
                    if len(parameter_list) > 1:
                        time_format = parameter_list[1]
                    try:
                        condition_value = str_to_time(condition_value, time_format)
                    except ValueError:
                        raise ValueError('操作符【{}】处理过程中出现错误，【{}】无法转换为datetime类型'.format(operator_character, condition_value))
                    try:
                        data_object = str_to_time(data, time_format)
                    except ValueError:
                        data_object = ValueError('Cannot change [%s] to datetime object' % data)
                        # raise ValueError('Cannot change [%s] to datetime object'%(data))
                else:
                    raise ValueError('操作符【{}】处理过程中出现错误，无效的转换类型【{}】'.format(operator_character, parameter_list[0]))
                expression = 'data_object %s condition_value' % first_operator
                if not isinstance(data_object, ValueError) and eval(expression):
                    is_matched = True
                    if first_operator != '!=':
                        match_count = 1

            # 正则表达式比较
            elif first_operator == 're':
                re_parameter = ''
                if parameter_list:
                    re_parameter = parameter_list[0]
                flags = generate_reg_flags(re_parameter)
                re_result = re.findall(condition_value, str(data), flags)
                match_count = len(re_result)
                if match_count > 0:
                    is_matched = True

            # json比较
            elif first_operator == 'json':
                try:
                    condition_object = json.loads(get_python_vaild_json(condition_value))
                except ValueError:
                    raise ValueError(
                        "Cannot change [{}] {} to json object.".format(condition_value, type(condition_value)))
                condition_object = restore_control_character_in_objecr(condition_object, restore_control_character)

                if isinstance(pre_data_object, (tuple, list, dict)):
                    data_object = pre_data_object
                else:
                    if isinstance(data, (tuple, list, dict)):
                        data_object = data
                    else:
                        try:
                            data_object = json.loads(get_python_vaild_json(data))
                        except ValueError:
                            raise ValueError("Cannot change [{}] {} to json object.".format(data, type(data)))

                list_exact_match = False
                dict_exact_match = False
                default_operator_list_ = None
                for parameter in parameter_list:
                    # 是否精确匹配list
                    if parameter == 'l':
                        list_exact_match = True
                    # 是否精确匹配dict
                    elif parameter == 'd':
                        dict_exact_match = True
                    # 是否默认使用正则表达式匹配
                    elif re.findall('^re\\[.*?\\]$|^re$', parameter, 0):
                        re_parameter_list = re.findall('\\[(.*?)\\]', parameter, 0)
                        if re_parameter_list:
                            default_operator_list_ = ['re', re_parameter_list[0]]
                        else:
                            default_operator_list_ = ['re', ]
                    elif parameter.strip() == '':
                        continue
                    else:
                        raise ValueError('操作符【{}】处理过程中出现错误，无效的参数【{}】'.format(operator_character, parameter))

                fo = FindObject(
                    list_exact_match, dict_exact_match, default_operator_list=default_operator_list_, logger=logger)
                is_matched, match_count, re_result, _error_msg = fo.find_object_in_object(condition_object, data_object)
                if not is_matched and _error_msg:
                    error_msg = _error_msg

            else:
                raise ValueError('Invalid operational character [' + first_operator + ']')
    except Exception as e:
        error_msg = getattr(e, 'msg', str(e))
        # logger.debug(error_msg)
    # logger.debug('is_matched: [%s], match_count: [%s]' % (find_result.is_matched, find_result.match_count))
    # logger.debug('find_result: \n%s' % find_result)
    return FindResult(
        is_matched, condition, data, match_count, condition_value, operator_list, data_object, re_result, error_msg)


# 获取正则表达式结果中第一个有效字符串
def get_first_str_in_re_result(re_result):
    if re_result:
        if isinstance(re_result, (list, tuple)):
            for result_ in re_result:
                if result_:
                    if isinstance(result_, (list, tuple)):
                        for result__ in result_:
                            if result__:
                                return str(result__)
                    else:
                        return str(result_)
        else:
            return str(re_result)
    return None


# 拆分“或”条件
def find_with_multiple_condition(condition, data, logger=logging.getLogger('py_test')):
    # logger = get_thread_logger()
    pass_group = []
    fail_group = []
    is_pass = False
    data_object = None
    union_count = 0
    if condition == '':
        is_pass = True
    else:
        condition = condition.split(sep='#||#')
        for single_condition in condition:
            if remove_line_break_and_blank_from_both_ends(single_condition) == '':  # 无内容时跳过
                continue
            else:
                union_count += 1
                single_condition = remove_line_break_from_both_ends(single_condition)  # 去掉两端换行，保留空格
                _p, _f, _data_object = find_with_multiple_condition_intersection(single_condition, data, union_count,
                                                                                 data_object, logger)

                if data_object is None and _data_object is not None:
                    data_object = _data_object
                if 0 == len(_f):
                    pass_group.append([union_count, _p, _f])
                    is_pass = True
                else:
                    fail_group.append([union_count, _p, _f])
    # logger.debug('Is Pass: %s' % is_pass)
    # logger.debug('Pass Group: %s' % pass_group)
    # logger.debug('Fail Group: %s' % fail_group)
    # logger.debug('Union Count: %s' % union_count)
    return is_pass, pass_group, fail_group, union_count, data_object


# 拆分“与”条件
def find_with_multiple_condition_intersection(
        condition, data, i, pre_data_object=None, logger=logging.getLogger('py_test')):
    condition = condition.split(sep='#&&#')
    p = []
    f = []
    intersection_count = 0
    data_object = None
    if isinstance(pre_data_object, (tuple, list, dict)):
        data_object = pre_data_object
    for single_condition in condition:
        if remove_line_break_and_blank_from_both_ends(single_condition) == '':  # 无内容时跳过
            continue
        else:
            intersection_count += 1
            single_condition = remove_line_break_from_both_ends(single_condition)  # 去掉两端换行，保留空格
            single_result = find_with_condition(single_condition, data, pre_data_object=data_object, logger=logger)
            if single_result.is_matched:
                p.append([str(i), str(intersection_count), single_result])
            else:
                f.append([str(i), str(intersection_count), single_result])
            if data_object is None and isinstance(single_result.data_object, (list, tuple, dict)):
                data_object = single_result.data_object

    return p, f, data_object
