import time
import datetime
import os
import traceback
from py_test.api_test import method
from py_test.general import vic_variables, test_result
from py_test.general import vic_method, import_test_data
from py_test.vic_tools import vic_eval
from py_test.vic_tools.vic_str_handle import change_digit_to_string, change_string_to_digit
from py_test.init_log import get_thread_logger

# 获取全局变量
global_variables = vic_variables.global_variables


def run(excel_file, tc_id=1, variables=None, result_dir=None, base_timeout=30, get_ss=False, level=0, dr=None,
        driver_info=None):
    logger = get_thread_logger()
    case_result = test_result.CaseResult(id_=tc_id, name=os.path.basename(excel_file), type_='api')
    case_result.start_time = datetime.datetime.now()
    step_start_time = case_result.start_time
    step_id = '1'
    full_id = "%s-%s" % (tc_id, step_id)
    step_data_dict = {
        'action': 'Initialize',
        'url': '',
        'headers': '',
        'body': '',
        'data': '',
    }
    if variables is None:
        variables = vic_variables.Variables()

    if level == 0:
        logger.info('【%s】\t%s' % (tc_id, excel_file))
    logger.info('【%s】\tInitialize|Loading ==> %s' % (full_id, excel_file))
    try:
        # 读取测试步骤数据
        step_data = import_test_data.get_excel_data(excel_file, 'Step')
        step_col_map = vic_method.get_excel_col_map(step_data)

        step_col_check_list = ('name', 'action', 'url', 'headers', 'body', 'data', 'timeout', 'skip', 'save_as',)
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
        case_result.add_step_result(step_result)
        case_result.error = e
        case_result.end_time = datetime.datetime.now()
        if logger.level < 10:
            raise
        return case_result
    else:
        step_result = test_result.StepResult(id_=step_id, name='Initialize ' + excel_file, status='o',
                                             message='Initialize Success', start_time=step_start_time,
                                             end_time=datetime.datetime.now(), data_dict=step_data_dict)
        case_result.add_step_result(step_result)

    for row in range(2, step_data['rows'] + 1):
        step_start_time = datetime.datetime.now()
        step_id = str(row)
        full_id = str(tc_id) + '-' + step_id
        step_data_dict = {
            'action': '',
            'url': '',
            'headers': '',
            'body': '',
            'data': '',
        }

        run_result = ('p', '')
        action = str()  # 初始化action为str
        try:
            step_name = change_digit_to_string(step_data[step_col_map['name'] + str(row)])
            action = change_digit_to_string(step_data[step_col_map['action'] + str(row)])
            # 兼容老版public step
            if action.lower() == 'public step':
                action = 'sub case'
            skip = change_digit_to_string(step_data[step_col_map['skip'] + str(row)])
            if action == '' or skip.lower() == 'yes':
                logger.info('【%s】\t%s|跳过' % (full_id, step_name))
                step_result = test_result.StepResult(id_=step_id, name=step_name, status='s', message='Skip',
                                                     start_time=step_start_time, end_time=datetime.datetime.now(),
                                                     data_dict=step_data_dict)
                case_result.add_step_result(step_result)
                continue
            url = change_digit_to_string(step_data[step_col_map['url'] + str(row)])
            if url != '':
                url = vic_method.replace_special_value(str_=url, variables=variables)
            headers = change_digit_to_string(step_data[step_col_map['headers'] + str(row)])
            if headers != '':
                headers = vic_method.replace_special_value(str_=headers, variables=variables)
            body = change_digit_to_string(step_data[step_col_map['body'] + str(row)])
            if body != '':
                body = vic_method.replace_special_value(str_=body, variables=variables)
            data = change_digit_to_string(step_data[step_col_map['data'] + str(row)])
            if data != '':
                data = vic_method.replace_special_value(str_=data, variables=variables)
            timeout = change_string_to_digit(step_data[step_col_map['timeout'] + str(row)])
            if timeout in ('', None):
                timeout = base_timeout
            save_as = change_digit_to_string(step_data[step_col_map['save_as'] + str(row)])
        except Exception as e:
            e_str = traceback.format_exc()
            logger.error('【%s】\t读取测试数据出错\n%s' % (full_id, e_str))
            step_data_dict['action'] = '【读取测试数据出错】'
            step_result = test_result.StepResult(id_=step_id, name='N/A', status='e', message=e_str,
                                                 start_time=step_start_time, end_time=datetime.datetime.now(),
                                                 data_dict=step_data_dict)
            case_result.add_step_result(step_result)
            case_result.error = e
            if logger.level < 10:
                raise
            break
        try:
            step_data_dict['action'] = action
            step_data_dict['url'] = url
            step_data_dict['headers'] = headers
            step_data_dict['body'] = body
            step_data_dict['data'] = data
            response_start_time = None
            response_end_time = None
            sub_result = None

            logger.info('【%s】\t%s|%s' % (full_id, step_name, action))

            if action.lower() == 'calculate variable':
                if data == '':
                    raise ValueError('Missing value in "data" column')
                    eo = vic_eval.EvalObject(data, vic_variables.get_variable_dict(variables))
                eval_success, eval_result, final_expression = eo.get_eval_result()
                if eval_success:
                    calculate_result = eval_result
                    run_result = ('p', final_expression + '/n' + str(eval_result))
                    if save_as != '':
                        variables.set_variable(save_as, calculate_result)
                else:
                    run_result = (
                        'f', 'Invalid expression [' + final_expression + ']\nInvalid value list: ' + str(eval_result))

            elif action.lower() in ('save variable', 'save global variable'):
                if save_as == '':
                    raise ValueError('Missing value in "save_as" column')
                if '#{str}#' not in data:  # 尝试转换data为数字
                    try:
                        data = int(data)
                    except ValueError:
                        try:
                            data = float(data)
                        except ValueError:
                            pass
                else:
                    data = data.replace('#{str}#', '')
                if action.lower() == 'save global variable':
                    msg = global_variables.set_variable(save_as, data)
                else:
                    msg = variables.set_variable(save_as, data)
                run_result = ('p', msg)

            elif action.lower() == 'compare variable':
                if data == '':
                    raise ValueError('Missing value in "data" column')
                eo = vic_eval.EvalObject(data, vic_variables.get_variable_dict(variables))
                eval_success, eval_result, final_expression = eo.get_eval_result()
                if eval_success:
                    if True == eval_result:  # eval_result有可能不是布尔值
                        run_result = ('p', final_expression + '/n' + str(eval_result))
                    else:
                        run_result = ('f', final_expression + '/n' + str(eval_result))
                else:
                    run_result = (
                        'f', 'Invalid expression [' + final_expression + ']\nInvalid value list: ' + str(eval_result))

            elif action.lower() == 'get':
                if url == '':
                    raise ValueError('Missing value in "url" column')
                response, str_content, response_start_time, response_end_time = method.send_http_request(
                    method='GET', url=url, headers=headers, body=body, timeout=timeout)
                if str_content is None:
                    run_result = ('f', 'Time out')
                else:
                    run_result = method.verify_http_response(expect=data, response=str_content)

            elif action.lower() == 'post':
                if url == '':
                    raise ValueError('Missing value in "url" column')
                response, str_content, response_start_time, response_end_time = method.send_http_request(
                    method='POST', url=url, headers=headers, body=body, timeout=timeout)
                if str_content is None:
                    run_result = ('f', 'Time out')
                else:
                    run_result = method.verify_http_response(expect=data, response=str_content)

            elif action.lower() == 'put':
                if url == '':
                    raise ValueError('Missing value in "url" column')
                response, str_content, response_start_time, response_end_time = method.send_http_request(
                    method='PUT', url=url, headers=headers, body=body, timeout=timeout)
                if str_content is None:
                    run_result = ('f', 'Time out')
                else:
                    run_result = method.verify_http_response(expect=data, response=str_content)

            elif action.lower() == 'delete':
                if url == '':
                    raise ValueError('Missing value in "url" column')
                response, str_content, response_start_time, response_end_time = method.send_http_request(
                    method='DELETE', url=url, headers=headers, body=body, timeout=timeout)
                if str_content is None:
                    run_result = ('f', 'Time out')
                else:
                    run_result = method.verify_http_response(expect=data, response=str_content)

            elif action.lower() == 'head':
                if url == '':
                    raise ValueError('Missing value in "url" column')
                response, str_content, response_start_time, response_end_time = method.send_http_request(
                    method='HEAD', url=url, headers=headers, body=body, timeout=timeout)
                if str_content is None:
                    run_result = ('f', 'Time out')
                else:
                    run_result = method.verify_http_response(expect=data, response=str_content)

            elif action.lower() == 'sleep':
                if data == '':
                    time.sleep(1)
                else:
                    try:
                        data = change_string_to_digit(data)
                    except ValueError:
                        raise ValueError('Invalid data in "data" column')
                    time.sleep(data)

            elif action.lower() == 'sub case':
                if data == '':
                    raise ValueError('请在data列填入子用例路径')

                original_para = dict()
                original_para['case_type'] = 'api'
                original_para['base_timeout'] = timeout
                original_para['get_ss'] = get_ss
                original_para['result_dir'] = result_dir
                original_para['driver'] = dr
                original_para['driver_info'] = driver_info
                level += 1
                sub_result = vic_method.run_sub_case(para_str=data, excel_file=excel_file, original_para=original_para,
                                                     tc_id=full_id, level=level, variables=variables)
                # 获取子用例中生成的driver
                dr = sub_result.data_dict.get('driver', dr)
                # 获取子用例中读取的dirver信息
                driver_info = sub_result.data_dict.get('driver_info', driver_info)
                level -= 1
                if sub_result.status == 'e':
                    e = sub_result.error
                    raise e
                elif sub_result.status == 'f':
                    run_result = ('f', sub_result)
                else:
                    run_result = ('p', sub_result)
            else:
                raise Exception('Invalid action ==> "' + action + '"')

            if response_start_time is not None and response_end_time is not None:
                step_data_dict['response_start_time'] = response_start_time
                step_data_dict['response_end_time'] = response_end_time

        except Exception as e:
            e_str = traceback.format_exc()
            logger.error('【%s】\t执行出错\n%s' % (full_id, e_str))
            if response_start_time is not None and response_end_time is not None:
                step_data_dict['response_start_time'] = response_start_time
                step_data_dict['response_end_time'] = response_end_time
            if action.lower() == 'sub case':
                step_result = test_result.StepResult(id_=step_id, name=step_name, status='e', message=sub_result,
                                                     start_time=step_start_time, end_time=datetime.datetime.now(),
                                                     data_dict=step_data_dict)
            else:
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
            if action.lower() == 'sub case':
                logger.warning('【%s】\t子用例执行失败' % full_id)
            else:
                logger.warning('【%s】\t执行失败 => %s' % (full_id, run_result[1]))
        else:
            logger.info('【%s】\t执行成功' % full_id)
        step_result = test_result.StepResult(id_=step_id, name=step_name, status=status, message=run_result[1],
                                             start_time=step_start_time, end_time=datetime.datetime.now(),
                                             data_dict=step_data_dict)
        case_result.add_step_result(step_result)
    if level == 0 and dr is not None:
        dr.quit()
        dr = None
    case_result.end_time = datetime.datetime.now()
    case_result.data_dict['driver'] = dr
    case_result.data_dict['driver_info'] = driver_info
    return case_result


if __name__ == '__main__':
    import logging
    from py_test.init_log import init_logger

    init_logger(log_level=logging.DEBUG, console_log_level=logging.INFO)
    logger = get_thread_logger()
    # base_dir = os.path.dirname(__file__)
    start_time = datetime.datetime.now()
    base_dir = 'D:/vic/debug/TC/oa'
    result_dir = 'D:/vic/debug/report'
    # excel_file_name = 'test_oa_ui_1_出差申请_普通用户-全流程.xlsx'
    # excel_file_name = 'test_oa_ui_出差申请_普通用户-发起.xlsx'
    excel_file_name = 'test3.xlsx'
    excel_file = os.path.join(base_dir, excel_file_name)
    case_result_list = list()
    case_result = run(excel_file=excel_file, result_dir=result_dir, base_timeout=5, get_ss=1, tc_id=1)
    case_result_list.append(case_result)

    end_time = datetime.datetime.now()
    report_title = 'api_debug'
    report_file_name = 'Automation_Test_Report_' + start_time.strftime("%Y-%m-%d_%H%M%S")
    report_name = vic_method.generate_case_report('api', result_dir, report_file_name, case_result_list, start_time,
                                                  end_time, report_title)

    logger.info('Report saved as %s' % report_name)
    logger.info('END')
