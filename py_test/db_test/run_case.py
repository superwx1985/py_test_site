import datetime
import os
import traceback
from py_test.db_test import method
from py_test.vic_tools.vic_str_handle import change_digit_to_string
from py_test.general import vic_variables, test_result
from py_test.general import vic_method, import_test_data
from py_test.general.thread_log import get_thread_logger


# 获取全局变量
global_variables = vic_variables.global_variables


def run(excel_file, tc_id=1, variables=None):
    logger = get_thread_logger()
    case_result = test_result.CaseResult(id_=tc_id, name=os.path.basename(excel_file), type_='db')
    case_result.start_time = datetime.datetime.now()
    step_start_time = case_result.start_time
    step_id = '1'
    full_id = "%s-%s" % (tc_id, step_id)
    step_data_dict = {
        'database_type': '',
        'database_host': '',
        'database_port': '',
        'database_name': '',
        'user': '',
        'password': '',
        'sql': '',
        'expect': '',
    }
    if variables is None:
        variables = vic_variables.Variables()

    logger.info('【%s】\t%s' % (tc_id, excel_file))
    logger.info('【%s】\tInitialize|Loading ==> %s' % (full_id, excel_file))
    try:
        # 读取测试步骤数据
        step_data = import_test_data.get_excel_data(excel_file, 'Step')
        step_col_map = vic_method.get_excel_col_map(step_data)

        step_col_check_list = (
            'name', 'database_type', 'database_host', 'database_port', 'database_name', 'user', 'password', 'sql',
            'expect', 'skip')
        for col in step_col_check_list:
            if col not in step_col_map:
                raise ValueError('测试用例文件【{}】的【{}】表缺少【{}】列'.format(excel_file, 'Variable', col))

        # 读取本地变量
        variable_date = import_test_data.get_excel_data(excel_file, 'Variable')
        for row in range(2, variable_date['rows'] + 1):
            name = change_digit_to_string(variable_date['A' + str(row)])
            value = change_digit_to_string(variable_date['B' + str(row)])
            value = vic_method.replace_special_value(str_=value, variables=variables)
            if name != '':
                variables.set_variable(name, value)
    except Exception as e:
        e_str = traceback.format_exc()
        logger.error('【%s】\t初始化出错\n%s' % (full_id, traceback.format_exc()))
        step_result = test_result.StepResult(id_=step_id, name='Initialize ' + excel_file, status='e', message=e_str,
                                             start_time=step_start_time, end_time=datetime.datetime.now(),
                                             data_dict=step_data_dict)
        if logger.level < 10:
            raise
        case_result.add_step_result(step_result)
        case_result.error = e
        case_result.end_time = datetime.datetime.now()
        return case_result
    else:
        step_result = test_result.StepResult(id_=step_id, name='Initialize ' + excel_file, status='o',
                                             message='Initialize Success',
                                             start_time=step_start_time, end_time=datetime.datetime.now(),
                                             data_dict=step_data_dict)
        case_result.add_step_result(step_result)

    for row in range(2, step_data['rows'] + 1):
        step_start_time = datetime.datetime.now()
        step_id = str(row)
        full_id = str(tc_id) + '-' + step_id
        step_data_dict = {
            'database_type': '',
            'database_host': '',
            'database_port': '',
            'database_name': '',
            'user': '',
            'password': '',
            'sql': '',
            'expect': '',
        }
        # run_result = ('p', '')
        try:
            step_name = change_digit_to_string(step_data[step_col_map['name'] + str(row)])
            database_type = change_digit_to_string(step_data[step_col_map['database_type'] + str(row)])
            skip = change_digit_to_string(step_data[step_col_map['skip'] + str(row)])
            if database_type == '' or skip.lower() == 'yes':
                logger.info('【%s】\t%s|跳过' % (full_id, step_name))
                step_result = test_result.StepResult(id_=step_id, name=step_name, status='s', message='Skip',
                                                     start_time=step_start_time, end_time=datetime.datetime.now(),
                                                     data_dict=step_data_dict)
                case_result.add_step_result(step_result)
                continue
            database_host = change_digit_to_string(step_data[step_col_map['database_host'] + str(row)])
            if database_host != '':
                database_host = vic_method.replace_special_value(str_=database_host, variables=variables)
            database_port = change_digit_to_string(step_data[step_col_map['database_port'] + str(row)])
            if database_port != '':
                database_port = vic_method.replace_special_value(str_=database_port, variables=variables)
            database_name = change_digit_to_string(step_data[step_col_map['database_name'] + str(row)])
            if database_name != '':
                database_name = vic_method.replace_special_value(str_=database_name, variables=variables)
            user = change_digit_to_string(step_data[step_col_map['user'] + str(row)])
            if user != '':
                user = vic_method.replace_special_value(str_=user, variables=variables)
            password = change_digit_to_string(step_data[step_col_map['password'] + str(row)])
            if password != '':
                password = vic_method.replace_special_value(str_=password, variables=variables)
            sql = change_digit_to_string(step_data[step_col_map['sql'] + str(row)])
            if sql != '':
                sql = vic_method.replace_special_value(str_=sql, variables=variables)
            expect = change_digit_to_string(step_data[step_col_map['expect'] + str(row)])
        except Exception as e:
            e_str = traceback.format_exc()
            logger.error('【%s】\t读取测试数据出错\n%s' % (full_id, e_str))
            step_result = test_result.StepResult(id_=step_id, name='N/A', status='e', message=e_str,
                                                 start_time=step_start_time, end_time=datetime.datetime.now(),
                                                 data_dict=step_data_dict)
            if logger.level < 10:
                raise
            case_result.add_step_result(step_result)
            case_result.error = e
            break
        try:
            step_data_dict['database_type'] = database_type
            step_data_dict['database_host'] = database_host
            step_data_dict['database_port'] = database_port
            step_data_dict['database_name'] = database_name
            step_data_dict['user'] = user
            step_data_dict['password'] = password
            step_data_dict['sql'] = sql
            step_data_dict['expect'] = expect

            logger.info('【%s】\t%s|%s' % (full_id, step_name, database_type))

            if database_type == '':
                raise ValueError('Missing value in "database_type" column')
            if database_host == '':
                raise ValueError('Missing value in "database_host" column')
            import cx_Oracle
            try:
                sql_result = method.get_sql_result(database_type=database_type, database_host=database_host,
                                                   database_port=database_port, database_name=database_name, user=user,
                                                   password=password, sql=sql)
            except cx_Oracle.DatabaseError:
                e_str = traceback.format_exc()
                run_result = ('f', '数据库连接报错：\n%s' % e_str)
            else:
                run_result = method.verify_sql_result(expect=expect, sql_result=sql_result)
        except Exception as e:
            e_str = traceback.format_exc()
            logger.error('【%s】\t执行出错\n%s' % (full_id, e_str))
            step_result = test_result.StepResult(id_=step_id, name=step_name, status='e', message=e_str,
                                                 start_time=step_start_time, end_time=datetime.datetime.now(),
                                                 data_dict=step_data_dict)
            case_result.add_step_result(step_result)
            case_result.error = e
            if logger.level < 10:
                raise
            break
        status = 'p'
        if run_result[0] == 'f':
            status = 'f'
            logger.warning('【%s】\t执行失败 => %s' % (full_id, run_result[1]))
        else:
            logger.info('【%s】\t执行成功' % full_id)
        step_result = test_result.StepResult(id_=step_id, name=step_name, status=status, message=run_result[1],
                                             start_time=step_start_time, end_time=datetime.datetime.now(),
                                             data_dict=step_data_dict)
        case_result.add_step_result(step_result)
    case_result.end_time = datetime.datetime.now()
    return case_result


if __name__ == '__main__':
    import logging
    from py_test.general.thread_log import init_logger
    init_logger(log_level=logging.DEBUG, console_log_level=logging.INFO)
    logger = get_thread_logger()
    # base_dir = os.path.dirname(__file__)
    start_time = datetime.datetime.now()
    base_dir = 'D:/vic/debug/TC/db'
    result_dir = 'D:/vic/debug/report'
    # excel_file_name = 'test_oa_ui_1_出差申请_普通用户-全流程.xlsx'
    # excel_file_name = 'test_oa_ui_出差申请_普通用户-发起.xlsx'
    excel_file_name = 'test_monitor_database_2.xlsx'
    excel_file = os.path.join(base_dir, excel_file_name)
    case_result_list = list()
    case_result = run(excel_file=excel_file, tc_id=1)
    case_result_list.append(case_result)

    end_time = datetime.datetime.now()
    report_title = 'db_debug'
    report_file_name = 'Automation_Test_Report_' + start_time.strftime("%Y-%m-%d_%H%M%S")
    report_name = vic_method.generate_case_report('db', result_dir, report_file_name, case_result_list, start_time,
                                                  end_time, report_title)

    logger.info('Report saved as %s' % report_name)
    logger.info('END')
