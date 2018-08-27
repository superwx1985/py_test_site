import datetime
import os
from py_test.general import vic_variables
from py_test.general import import_test_data
from py_test.vic_tools import vic_eval, vic_generate_str
from py_test.vic_tools import vic_excel_col_change
from py_test.general.vic_log import get_thread_logger


# 替换字符串内的变量
def replace_parameter_in_str(str_, start_str, end_str, f, variables):
    logger = get_thread_logger()
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
            value = str(f(parameter, variables))  # 替换
        logger.debug('%s ======> %s' % (str_[start_index:end_index + len(end_str)], value))
        str_ = str_[0:start_index] + value + str_[end_index + len(end_str):]  # 为防止替换了相同的内容，采用拼接的方法
    logger.debug('end replace: [%s]' % str_)
    return str_


# 整合参数方便调用
def replace_special_value(str_, variables):
    str_ = replace_parameter_in_str(str_=str_, start_str='${', end_str='}$', f=select_func, variables=variables)
    return str_


# 通过操作符选择变量处理方式
def select_func(str_, variables):
    if '|' not in str_:
        value = vic_variables.get_str(str_, variables)
    else:
        new_str = str_.split(sep='|')
        f = new_str[0]
        parameter = new_str[1]
        if f == 'r':
            value = vic_generate_str.get_random_func(parameter)
        elif f == 't':
            value = vic_generate_str.get_time_func(parameter)
        elif f == 'ts':
            value = vic_generate_str.get_timestamp_func(parameter)
        elif f == 'tst':
            value = vic_generate_str.timestamp_to_time_func(parameter)
        elif f == 'url':
            value = vic_generate_str.encode_url_func(parameter)
        elif f == 'cal':
            eo = vic_eval.EvalObject(parameter, vic_variables.get_variable_dict(variables))
            success, eval_result, final_expression = eo.get_eval_result()
            if success:
                value = str(eval_result)
            else:
                value = 'Calculate Error!\nExpression:\n' + final_expression + '\n' + str(eval_result)
        elif f == 'uuid':
            value = vic_generate_str.get_uuid()
        elif f == 'slice':
            value = vic_generate_str.get_slice(parameter)
        else:
            raise ValueError('[' + f + '] is an invalid functions code')
    return value


# 在字典中读取数据，key不存在则返回空
def load_data_in_dict(dict_, key):
    try:
        return dict_[key]
    except KeyError:
        return ''


# 从excel列表读取相同工作表的数据
def load_data_in_excel_list(original_excel_file, excel_list, sheet_name):
    data_dict = dict()
    for excel_file in excel_list:
        if excel_file == '':
            continue
        if not os.path.isabs(excel_file):
            excel_file = os.path.join(os.path.dirname(original_excel_file), excel_file)
        data_dict[excel_file] = import_test_data.get_excel_data(excel_file, sheet_name)
    return data_dict


# 获取excel工作表内标题和列名对应关系
def get_excel_col_map(excel_data):
    col_map = dict()
    for col in range(1, excel_data['columns'] + 1):
        excel_col = vic_excel_col_change.dec_to_excel_col(col)
        col_map[excel_data['{}1'.format(excel_col)]] = excel_col
    return col_map


# 读取公共内容
def load_public_data(variable_objects, global_variables, public_elements):
    # 读取公共变量表，保存到全局变量中
    for obj in variable_objects:
        value = replace_special_value(obj.value, global_variables)
        global_variables.set_variable(obj.name, value)

    # 读取公共元素表，保存到公共元素组中
    # todo()
    # data = dict()
    # if data:
    #     col_map = get_excel_col_map(data)
    #     col_check_list = ('name', 'by', 'locator')
    #     for col in col_check_list:
    #         if col not in col_map:
    #             raise ValueError('公共配置文件【{}】的【{}】表缺少【{}】列'.format(excel_file, 'Element', col))
    #     for row in range(2, data['rows'] + 1):
    #         name = str(load_data_in_dict(data, '{}{}'.format(col_map['name'], row)))
    #         if name != '':
    #             by = str(load_data_in_dict(data, '{}{}'.format(col_map['by'], row)))
    #             by = replace_special_value(by, global_variables)
    #             locator = str(load_data_in_dict(data, '{}{}'.format(col_map['locator'], row)))
    #             locator = replace_special_value(locator, global_variables)
    #             public_elements.add_element_info(name, vic_public_elements.ElementInfo(by, locator))


# 创建目录
def check_and_mkdir(file_path, base_path=os.getcwd()):
    _path, _name = os.path.split(file_path)

    if not os.path.isabs(_path):
        if _path:
            _path = os.path.join(base_path, _path)
        else:
            _path = base_path

    if not os.path.exists(_path):
        try:
            os.makedirs(_path)
        except OSError as e:
            print('%s[%s]' % (e.strerror, e.filename))
            _path = base_path
            if not os.path.exists(_path):
                try:
                    os.makedirs(_path)
                except OSError as e:
                    print('%s[%s]' % (e.strerror, e.filename))
                    _path = os.getcwd()

    _name_result = check_name(_name)
    if not _name_result[0]:
        print(_name_result[1])
        _name_suffix = os.path.splitext(_name)[1]
        _name = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f") + _name_suffix
    return _path, _name


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


# 获取子用例参数
def get_sub_case_para(para_str):
    para_list = para_str.split(',')
    para_dict = dict()

    for p in para_list:
        p = p.split('=')
        if len(p) == 2:
            para_dict[p[0].strip()] = p[1].strip()
        else:
            raise ValueError('错误的子用例参数【%s】' % para_str)

    for k, v in para_dict.items():
        if k.lower() in ('get_ss', 'debug'):
            if v.lower() in ('false', '0'):
                para_dict[k] = False
            else:
                para_dict[k] = True
        elif k.lower() == 'base_timeout':
            para_dict[k] = float(v)

    return para_dict


# 子用例调用
def run_sub_case(para_str, excel_file, original_para, tc_id, level, variables):
    sub_case_para = dict()
    # 判断是否有分隔符
    if '|' in para_str:
        para_str_list = para_str.split('|')
        sub_tc_path = para_str_list[0].strip()
        sub_case_para = get_sub_case_para(para_str_list[1])
    else:
        sub_tc_path = para_str.strip()
    # 判断是否绝对路径
    if not os.path.isabs(sub_tc_path):
        sub_tc_path = os.path.join(os.path.dirname(excel_file), sub_tc_path)
    # 获取子用例类型及运行参数
    if 'case_type' in sub_case_para and sub_case_para['case_type'] in ('api', 'ui', 'db'):
        sub_case_type = sub_case_para['case_type']
    else:
        sub_case_type = original_para['case_type']
    sub_base_timeout = sub_case_para.get('base_timeout', original_para.get('base_timeout', None))
    sub_get_ss = sub_case_para.get('get_ss', original_para.get('get_ss', True))
    sub_driver = original_para.get('driver', None)
    sub_driver_info = original_para.get('driver_info', None)
    # 执行并返回子用例结果
    if sub_case_type == 'ui':
        sub_result_dir = os.path.join(original_para['result_dir'], 'sub_case')
        if sub_base_timeout is None:
            sub_base_timeout = 10
        from py_test.ui_test.run_case import run
        return run(excel_file=sub_tc_path, tc_id=tc_id, variables=variables, result_dir=sub_result_dir,
                   base_timeout=sub_base_timeout, get_ss=sub_get_ss, level=level, dr=sub_driver,
                   driver_info=sub_driver_info)
    elif sub_case_type == 'api':
        sub_result_dir = os.path.join(original_para['result_dir'], 'sub_case')
        if sub_base_timeout is None:
            sub_base_timeout = 30
        from py_test.api_test import run
        return run(excel_file=sub_tc_path, tc_id=tc_id, variables=variables, result_dir=sub_result_dir,
                   base_timeout=sub_base_timeout, get_ss=sub_get_ss, level=level, dr=sub_driver,
                   driver_info=sub_driver_info)
    elif sub_case_type == 'db':
        from py_test.db_test import run
        return run(excel_file=sub_tc_path, tc_id=tc_id, variables=variables)


# 生成用例报告
def generate_case_report(case_type, result_dir, report_file_name, case_result_list, start_time, end_time, report_title):
    if case_type == 'ui':
        from py_test.ui_test.generate_html_report import generate_report
    elif case_type == 'api':
        from py_test.api_test.generate_html_report import generate_report
    elif case_type == 'db':
        from py_test.db_test.generate_html_report import generate_report
    else:
        raise ValueError('{}类型的测试用例无对应的生成报告方法'.format(case_type))
    report_name = generate_report(result_dir=result_dir, report_file_name=report_file_name,
                                  case_result_list=case_result_list, start_time=start_time, end_time=end_time,
                                  report_title=report_title)
    return report_name
