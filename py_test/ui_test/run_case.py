import datetime
import time
import os
import traceback
import uuid
from py_test.general import vic_variables, vic_public_elements, test_result
from py_test.general import vic_method, import_test_data
from py_test.ui_test import method
from selenium.common.exceptions import UnexpectedAlertPresentException, NoSuchElementException
from py_test.vic_tools import vic_eval
from py_test.vic_tools.vic_str_handle import change_digit_to_string, change_string_to_digit
from py_test.general.thread_log import get_thread_logger

# 获取全局变量
global_variables = vic_variables.global_variables
# 获取公共元素组
public_elements = vic_public_elements.public_elements


def run(excel_file, tc_id=1, variables=None, result_dir=None, base_timeout=10, get_ss=False, level=0, dr=None,
        driver_info=None):
    logger = get_thread_logger()
    # 创建截图保存目录
    if result_dir == None:
        result_dir = os.path.dirname(excel_file)
    if not os.path.exists(result_dir):
        # 防止多线程运行时，创建同名文件夹报错
        try:
            os.makedirs(result_dir)
        except FileExistsError:
            pass
    case_result = test_result.CaseResult(id_=tc_id, name=os.path.basename(excel_file), type_='ui')
    case_result.start_time = datetime.datetime.now()
    step_start_time = case_result.start_time
    step_id = '1'
    full_id = "%s-%s" % (tc_id, step_id)
    step_data_dict = {
        'action': 'Initialize',
        'by': '',
        'locator': '',
        'index': '',
        'base_element': '',
        'data': '',
        'save_as': '',
        'timeout': '',
        'ss_name': '',
        'last_url': '',
        'special_action': '',
        'alert_handle': '',
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

        step_col_check_list = (
            'name', 'action', 'by', 'locator', 'index', 'data', 'timeout', 'skip', 'save_as', 'base_element',)
        for col in step_col_check_list:
            if col not in step_col_map:
                raise ValueError('测试用例文件【{}】的【{}】表缺少【{}】列'.format(excel_file, 'Variable', col))

        # 读取本地变量
        variable_date = import_test_data.get_excel_data(excel_file, 'Variable')
        for row in range(2, variable_date['rows'] + 1):
            name = change_digit_to_string(variable_date['A' + str(row)])
            value = change_digit_to_string(variable_date['B' + str(row)])
            value = vic_method.replace_special_value(value, variables)
            if name != '':
                variables.set_variable(name, value)

        config_data = import_test_data.get_excel_data(excel_file, 'Config')

        if level == 0 or dr is None:
            driver_info = dict()
            driver_info['driver_type'] = vic_method.replace_special_value(
                change_digit_to_string(vic_method.load_data_in_dict(config_data, 'B1')), variables)
            driver_info['browser_type'] = vic_method.replace_special_value(
                change_digit_to_string(vic_method.load_data_in_dict(config_data, 'C1')), variables)
            driver_info['browser_size'] = vic_method.replace_special_value(
                change_digit_to_string(vic_method.load_data_in_dict(config_data, 'C2')), variables)
            driver_info['browser_width'] = vic_method.replace_special_value(
                change_digit_to_string(vic_method.load_data_in_dict(config_data, 'E2')), variables)
            driver_info['browser_height'] = vic_method.replace_special_value(
                change_digit_to_string(vic_method.load_data_in_dict(config_data, 'G2')), variables)
            driver_info['browser_profile'] = vic_method.replace_special_value(
                change_digit_to_string(vic_method.load_data_in_dict(config_data, 'I2')), variables)
            if driver_info['driver_type'].lower() == 'remote':
                driver_info['browser_ip'] = vic_method.replace_special_value(
                    change_digit_to_string(vic_method.load_data_in_dict(config_data, 'E1')), variables)
                driver_info['browser_port'] = vic_method.replace_special_value(
                    change_digit_to_string(vic_method.load_data_in_dict(config_data, 'G1')), variables)
            assert (driver_info['driver_type'] != '' and driver_info['browser_type'] != ''), 'missing browser config'
            dr = method.get_driver(driver_info)

    except Exception as e:
        e_str = traceback.format_exc()
        logger.error('【%s】\t初始化出错\n%s' % (full_id, traceback.format_exc()))
        step_result = test_result.StepResult(id_=step_id, name='Initialize ' + excel_file, status='e',
                                             message=e_str, start_time=step_start_time,
                                             end_time=datetime.datetime.now(), data_dict=step_data_dict)
        if logger.level < 10:
            raise
        case_result.add_step_result(step_result)
        case_result.error = e
        case_result.end_time = datetime.datetime.now()
        return case_result
    else:
        step_data_dict['locator'] = excel_file
        if driver_info['driver_type'].lower() == 'local':
            step_data_dict['by'] = driver_info['driver_type'] + '|' + driver_info['browser_type']
            step_result = test_result.StepResult(id_=step_id, name='Initialize ' + excel_file, status='o',
                                                 message='Initialize Success', start_time=step_start_time,
                                                 end_time=datetime.datetime.now(), data_dict=step_data_dict)
        else:
            step_data_dict['by'] = driver_info['driver_type'] + '|' + driver_info[
                'browser_type'] + '|' + driver_info['browser_ip'] + ':' + driver_info['browser_port']
            step_result = test_result.StepResult(id_=step_id, name='Initialize ' + excel_file, status='o',
                                                 message='Initialize Success', start_time=step_start_time,
                                                 end_time=datetime.datetime.now(), data_dict=step_data_dict)
        case_result.add_step_result(step_result)

    last_alert_handle = ''  # 初始化弹窗处理方式
    for row in range(2, step_data['rows'] + 1):
        step_start_time = datetime.datetime.now()
        step_id = str(row)
        full_id = str(tc_id) + '-' + step_id
        ss_name = ''
        alert_handle = last_alert_handle
        # 如有弹窗则处理弹窗
        try:
            last_url = dr.current_url
        except UnexpectedAlertPresentException:
            alert_handle_text, alert_text = method.confirm_alert(dr=dr, alert_handle=alert_handle, timeout=timeout)
            logger.info('【{}】\t处理了一个弹窗，处理方式为【{}】，弹窗内容为\n{}'.format(full_id, alert_handle_text, alert_text))
        if last_url == 'data:,':
            last_url = ''
        step_data_dict = {
            'action': '',
            'by': '',
            'locator': '',
            'index': '',
            'base_element': '',
            'data': '',
            'save_as': '',
            'timeout': '',
            'ss_name': ss_name,
            'last_url': last_url,
            'special_action': '',
            'alert_handle': '',
        }
        run_result = ('p', '')
        is_verify_step = False
        elements = list()
        fail_elements = list()
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
            by = change_digit_to_string(step_data[step_col_map['by'] + str(row)])
            locator = change_digit_to_string(step_data[step_col_map['locator'] + str(row)])
            if locator != '':
                locator = vic_method.replace_special_value(locator, variables)
            index = change_string_to_digit(step_data[step_col_map['index'] + str(row)])
            if index in ('', None):
                index = ''
            else:
                index = round(index)
            data = change_digit_to_string(step_data[step_col_map['data'] + str(row)])
            if data != '':
                data = vic_method.replace_special_value(data, variables)
            timeout = base_timeout
            case_timeout = change_string_to_digit(step_data[step_col_map['timeout'] + str(row)])
            if case_timeout not in ('', None):
                timeout = case_timeout
            save_as = change_digit_to_string(step_data[step_col_map['save_as'] + str(row)])
            base_element = change_digit_to_string(step_data[step_col_map['base_element'] + str(row)])
            if base_element != '':
                base_element = vic_method.replace_special_value(base_element, variables)
                base_element = vic_variables.get_elements(base_element, variables)[0]
            if 'special_action' in step_col_map:
                special_action = change_digit_to_string(step_data[step_col_map['special_action'] + str(row)])
            else:
                special_action = ''
            if 'alert_handle' in step_col_map:
                alert_handle = change_digit_to_string(step_data[step_col_map['alert_handle'] + str(row)])
            else:
                alert_handle = ''
            last_alert_handle = alert_handle
        except Exception as e:
            e_str = traceback.format_exc()
            logger.error('【%s】\t读取测试数据出错\n%s' % (full_id, e_str))
            step_data_dict['action'] = '【读取测试数据出错】'
            try:
                if dr is not None and action.lower() != 'sub case' and get_ss:
                    ss_name = 'screenshot_{}_{}.png'.format(full_id, uuid.uuid1())
                    method.get_current_screenshot(dr=dr, result_dir=result_dir, ss_name=ss_name)
            except Exception:
                e2_str = traceback.format_exc()
                ss_name = ''
                logger.error('当前URL为【%s】， 截图出错\n%s' % (last_url, e2_str))
                step_data_dict['ss_name'] = ss_name
                step_result = test_result.StepResult(id_=step_id, name='N/A', status='e', message=e_str,
                                                     start_time=step_start_time, end_time=datetime.datetime.now(),
                                                     data_dict=step_data_dict)
                if logger.level < 10:
                    raise
            else:
                if dr is not None:
                    dr.quit()
                    dr = None
                step_data_dict['action'] = '(Loading test data error)'
                step_data_dict['ss_name'] = ss_name
                step_data_dict['last_url'] = last_url
                step_result = test_result.StepResult(id_=step_id, name='N/A', status='e', message=e_str,
                                                     start_time=step_start_time, end_time=datetime.datetime.now(),
                                                     data_dict=step_data_dict)
            if logger.level < 10:
                raise
            case_result.add_step_result(step_result)
            case_result.error = e
            break
        try:
            step_data_dict['action'] = action
            step_data_dict['by'] = by
            step_data_dict['locator'] = locator
            step_data_dict['index'] = index
            step_data_dict['base_element'] = base_element
            step_data_dict['data'] = data
            step_data_dict['save_as'] = save_as
            step_data_dict['timeout'] = timeout
            step_data_dict['special_action'] = special_action
            step_data_dict['alert_handle'] = alert_handle

            dr.implicitly_wait(timeout)
            dr.set_page_load_timeout(timeout)
            dr.set_script_timeout(timeout)
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
                        'f', 'Invaild expression [' + final_expression + ']\nInvalid value list: ' + str(eval_result))

            elif action.lower() in ('save variable', 'save global variable'):
                if save_as == '':
                    raise ValueError('Missing value in "save_as" column')
                if data == '' and by == '' and locator == '':
                    if action.lower() == 'save global variable':
                        msg = global_variables.set_variable(save_as, elements)
                    else:
                        msg = variables.set_variable(save_as, elements)
                elif data != '':
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
                elif by != '' and locator != '':
                    if dr is None:
                        raise ValueError('browser was uninitialized')
                    run_result, elements = method.wait_for_element_present(dr=dr, by=by, locator=locator,
                                                                           timeout=timeout, base_element=base_element)
                    if run_result[0] == 'f':
                        raise NoSuchElementException(run_result[1])
                    if action.lower() == 'save global variable':
                        msg = global_variables.set_variable(save_as, elements)
                    else:
                        msg = variables.set_variable(save_as, elements)
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

            elif action.lower() == 'go to url':
                if data == '' and locator == '':
                    raise ValueError('请在data列填入要打开的URL地址')
                elif data == '':
                    data = locator
                method.go_to_url(dr, data)

            elif action.lower() == 'refresh':
                dr.refresh()

            elif action.lower() == 'forward':
                dr.forward()

            elif action.lower() == 'back':
                dr.back()

            elif action.lower() == 'sleep':
                if data == '':
                    time.sleep(1)
                else:
                    try:
                        data = change_string_to_digit(data)
                    except ValueError:
                        raise ValueError('Invalid data in "data" column')
                    time.sleep(data)

            elif action.lower() == 'screenshot':
                if data != '':
                    ss_name = data
                else:
                    ss_name = 'screenshot_{}.png'.format(uuid.uuid1())
                file_path = method.get_screenshot_full_name(ss_name, result_dir)
                if by != '' and locator != '':
                    run_result_temp, visible_elements, elements_all = method.wait_for_element_visible(dr=dr, by=by,
                                                                                                      locator=locator,
                                                                                                      timeout=timeout,
                                                                                                      base_element=base_element)
                    if len(visible_elements) > 0:
                        highlight_elements_map = method.highlight(dr, visible_elements, 'yellow')
                        method.get_screenshot_on_element(dr, visible_elements[0], file_path)
                        method.cancel_highlight(dr, highlight_elements_map)
                    else:
                        run_result = ['f', '无法截图，因为' + run_result_temp[1]]
                else:
                    if case_timeout in ('', None):
                        case_timeout = 0.1
                    method.get_screenshot(dr, file_path, 100, case_timeout, 0, 10000)
                logger.info('截图保存为%s' % ss_name)

            elif action.lower() == 'click':
                if by == '' or locator == '':
                    raise ValueError('Missing value in "by" or "locator" column')
                variable_elements = None
                origin_locator = None
                if by == 'variable':
                    variable_elements = vic_variables.get_elements(locator, variables)
                elif by == 'public element':
                    origin_locator = locator
                    by, locator = method.get_public_elements(locator, public_elements)
                run_result, elements = method.try_to_click(dr=dr, by=by, locator=locator, timeout=timeout, index_=index,
                                                           base_element=base_element,
                                                           variable_elements=variable_elements)
                if origin_locator is not None:
                    step_data_dict['locator'] = '%s [%s|%s]' % (origin_locator, by, locator)
                if save_as != '':
                    variables.set_variable(save_as, elements)

            elif action.lower() == 'double click':
                if by == '' or locator == '':
                    raise ValueError('Missing value in "by" or "locator" column')
                variable_elements = None
                origin_locator = None
                if by == 'variable':
                    variable_elements = vic_variables.get_elements(locator, variables)
                elif by == 'public element':
                    origin_locator = locator
                    by, locator = method.get_public_elements(locator, public_elements)
                run_result, elements = method.try_to_double_click(dr=dr, by=by, locator=locator, timeout=timeout,
                                                                  index_=index, base_element=base_element,
                                                                  variable_elements=variable_elements)
                if origin_locator is not None:
                    step_data_dict['locator'] = '%s [%s|%s]' % (origin_locator, by, locator)
                if save_as != '':
                    variables.set_variable(save_as, elements)

            elif action.lower() == 'enter':
                if by == '' or locator == '':
                    raise ValueError('Missing value in "by" or "locator" column')
                variable_elements = None
                origin_locator = None
                if by == 'variable':
                    variable_elements = vic_variables.get_elements(locator, variables)
                elif by == 'public element':
                    origin_locator = locator
                    by, locator = method.get_public_elements(locator, public_elements)
                run_result, elements = method.try_to_enter(dr=dr, by=by, locator=locator, data=data, timeout=timeout,
                                                           index_=index, base_element=base_element,
                                                           variable_elements=variable_elements)
                if origin_locator is not None:
                    step_data_dict['locator'] = '%s [%s|%s]' % (origin_locator, by, locator)
                if save_as != '':
                    variables.set_variable(save_as, elements)

            elif action.lower() == 'special action':
                variable_elements = None
                origin_locator = None
                if by == 'variable':
                    variable_elements = vic_variables.get_elements(locator, variables)
                elif by == 'public element':
                    origin_locator = locator
                    by, locator = method.get_public_elements(locator, public_elements)
                run_result, elements = method.perform_special_action(dr=dr, by=by, locator=locator, data=data,
                                                                     timeout=timeout, index_=index,
                                                                     base_element=base_element,
                                                                     special_action=special_action, variables=variables,
                                                                     variable_elements=variable_elements)
                if origin_locator is not None:
                    step_data_dict['locator'] = '%s [%s|%s]' % (origin_locator, by, locator)
                if save_as != '':
                    variables.set_variable(save_as, elements)

            elif action.lower() == 'verify text':
                if data == '':
                    raise ValueError('Missing value in "data" column')
                if by != '' and locator != '':
                    variable_elements = None
                    origin_locator = None
                    if by == 'variable':
                        variable_elements = vic_variables.get_elements(locator, variables)
                    elif by == 'public element':
                        origin_locator = locator
                        by, locator = method.get_public_elements(locator, public_elements)
                    run_result, elements, fail_elements = method.wait_for_text_present_with_locator(dr=dr, by=by,
                                                                                                    locator=locator,
                                                                                                    text=data,
                                                                                                    timeout=timeout,
                                                                                                    index_=index,
                                                                                                    base_element=base_element,
                                                                                                    variable_elements=variable_elements)
                    if origin_locator is not None:
                        step_data_dict['locator'] = '%s [%s|%s]' % (origin_locator, by, locator)
                elif by != '' or locator != '':
                    raise ValueError('The "by" and "locator" column should come in pairs')
                else:
                    run_result, elements = method.wait_for_text_present(dr=dr, text=data, timeout=timeout,
                                                                        base_element=base_element)
                if save_as != '':
                    variables.set_variable(save_as, elements)
                is_verify_step = True

            elif action.lower() == 'verify element show':
                if by == '' or locator == '':
                    raise ValueError('Missing value in "by" or "locator" column')
                variable_elements = None
                origin_locator = None
                if by == 'variable':
                    variable_elements = vic_variables.get_elements(locator, variables)
                elif by == 'public element':
                    origin_locator = locator
                    by, locator = method.get_public_elements(locator, public_elements)
                if data == '':
                    run_result, elements, elements_all = method.wait_for_element_visible(dr=dr, by=by, locator=locator,
                                                                                         timeout=timeout,
                                                                                         base_element=base_element,
                                                                                         variable_elements=variable_elements)
                else:
                    run_result, elements = method.wait_for_element_visible_with_data(dr=dr, by=by, locator=locator,
                                                                                     data=data, timeout=timeout,
                                                                                     base_element=base_element,
                                                                                     variable_elements=variable_elements)
                if origin_locator is not None:
                    step_data_dict['locator'] = '%s [%s|%s]' % (origin_locator, by, locator)
                if save_as != '':
                    variables.set_variable(save_as, elements)
                is_verify_step = True

            elif action.lower() == 'verify element hide':
                if by == '' or locator == '':
                    raise ValueError('Missing value in "by" or "locator" column')
                variable_elements = None
                origin_locator = None
                if by == 'variable':
                    variable_elements = vic_variables.get_elements(locator, variables)
                elif by == 'public element':
                    origin_locator = locator
                    by, locator = method.get_public_elements(locator, public_elements)
                run_result, elements = method.wait_for_element_disappear(dr=dr, by=by, locator=locator, timeout=timeout,
                                                                         base_element=base_element,
                                                                         variable_elements=variable_elements)
                if origin_locator is not None:
                    step_data_dict['locator'] = '%s [%s|%s]' % (origin_locator, by, locator)
                if save_as != '':
                    variables.set_variable(save_as, elements)
                is_verify_step = True

            elif action.lower() == 'verify url':
                if data == '':
                    raise ValueError('Missing value in "data" column')
                run_result, new_url = method.wait_for_page_redirect(dr=dr, new_url=data, timeout=timeout)
                is_verify_step = True

            elif action.lower() == 'switch to window':
                run_result, new_window_handle = method.try_to_switch_to_window(dr=dr, by=by, locator=locator,
                                                                               timeout=timeout,
                                                                               base_element=base_element)

            elif action.lower() == 'close window':
                dr.close()

            elif action.lower() == 'reset browser':
                if dr is not None:
                    dr.quit()
                    dr = method.get_driver(driver_info)

            elif action.lower() == 'switch to frame':
                run_result = method.try_to_switch_to_frame(dr=dr, by=by, locator=locator, index=index, timeout=timeout,
                                                           base_element=base_element)

            elif action.lower() == 'switch to default content':
                dr.switch_to.default_content()

            elif action.lower() == 'run js':
                if data == '':
                    raise ValueError('Missing value in "data" column')
                variable_elements = None
                origin_locator = None
                if by == 'variable':
                    variable_elements = vic_variables.get_elements(locator, variables)
                elif by == 'public element':
                    origin_locator = locator
                    by, locator = method.get_public_elements(origin_locator, public_elements)
                run_result, js_result = method.run_js(dr=dr, by=by, locator=locator, data=data, timeout=timeout,
                                                      index_=index, base_element=base_element,
                                                      variable_elements=variable_elements)
                if origin_locator is not None:
                    step_data_dict['locator'] = '%s [%s|%s]' % (origin_locator, by, locator)
                if save_as != '':
                    variables.set_variable(save_as, js_result)

            elif action.lower() == 'verify js return':
                if data == '':
                    raise ValueError('Missing value in "data" column')
                variable_elements = None
                origin_locator = None
                if by == 'variable':
                    variable_elements = vic_variables.get_elements(locator, variables)
                elif by == 'public element':
                    origin_locator = locator
                    by, locator = method.get_public_elements(origin_locator, public_elements)
                run_result, js_result = method.run_js(dr=dr, by=by, locator=locator, data=data, timeout=timeout,
                                                      index_=index, base_element=base_element,
                                                      variable_elements=variable_elements)
                if js_result != True:
                    run_result = ('f', run_result[1])
                if origin_locator is not None:
                    step_data_dict['locator'] = '%s [%s|%s]' % (origin_locator, by, locator)
                if save_as != '':
                    variables.set_variable(save_as, js_result)

            elif action.lower() == 'sub case':
                if data == '':
                    raise ValueError('请在data列填入子用例路径')

                original_para = dict()
                original_para['case_type'] = 'ui'
                original_para['base_timeout'] = timeout
                original_para['get_ss'] = get_ss
                original_para['result_dir'] = result_dir
                original_para['driver'] = dr
                original_para['driver_info'] = driver_info
                level += 1
                sub_result = vic_method.run_sub_case(para_str=data, excel_file=excel_file,
                                                     original_para=original_para, tc_id=full_id, level=level,
                                                     variables=variables)
                # 获取子用例中生成的driver
                dr = sub_result.data_dict.get('driver', dr)
                level -= 1
                if sub_result.status == 'e':
                    e = sub_result.error
                    raise e
                elif sub_result.status == 'f':
                    run_result = ('f', sub_result)
                else:
                    run_result = ('p', sub_result)
            else:
                raise Exception('Invalid action [%s]' % action)

            # 如有弹窗则处理弹窗
            try:
                last_url = dr.current_url
            except UnexpectedAlertPresentException:
                alert_handle_text, alert_text = method.confirm_alert(dr=dr, alert_handle=alert_handle, timeout=timeout)
                logger.info('【{}】\t处理了一个弹窗，处理方式为【{}】，弹窗内容为\n{}'.format(full_id, alert_handle_text, alert_text))
            if last_url == 'data:,':
                last_url = ''

        except Exception as e:
            e_str = traceback.format_exc()
            logger.error('【%s】\t执行出错\n%s' % (full_id, e_str))
            try:
                if dr is not None and action.lower() != 'sub case' and get_ss:
                    last_url = dr.current_url
                    ss_name = 'screenshot_{}_{}.png'.format(full_id, uuid.uuid1())
                    method.get_current_screenshot(dr=dr, result_dir=result_dir, ss_name=ss_name)
            except Exception as e2:
                e2_str = traceback.format_exc()
                ss_name = ''
                logger.error('当前URL为【%s】， 截图出错\n%s' % (last_url, e2_str))
            step_data_dict['ss_name'] = ss_name
            step_data_dict['last_url'] = last_url
            if action.lower() == 'sub case':
                step_result = test_result.StepResult(id_=step_id, name=step_name, status='e', message=sub_result,
                                                     start_time=step_start_time, end_time=datetime.datetime.now(),
                                                     data_dict=step_data_dict)
            else:
                step_result = test_result.StepResult(id_=step_id, name=step_name, status='e', message=e_str,
                                                     start_time=step_start_time, end_time=datetime.datetime.now(),
                                                     data_dict=step_data_dict)
            if logger.level < 10:
                raise
            if dr is not None:
                dr.quit()
                dr = None
            case_result.add_step_result(step_result)
            case_result.error = e
            break
        status = 'p'
        if run_result[0] == 'f':
            status = 'f'
            if action.lower() == 'sub case':
                logger.warning('【%s】\t子用例执行失败' % full_id)
            else:
                logger.warning('【%s】\t执行失败 => %s' % (full_id, run_result[1]))
            try:
                if get_ss:
                    highlight_elements_map = {}
                    if len(elements) > 0:
                        highlight_elements_map = method.highlight(dr, elements, 'green')
                    if len(fail_elements) > 0:
                        highlight_elements_map = {**highlight_elements_map,
                                                  **method.highlight(dr, fail_elements, 'red')}
                    ss_name = 'screenshot_{}_{}.png'.format(full_id, uuid.uuid1())
                    method.get_current_screenshot(dr=dr, result_dir=result_dir, ss_name=ss_name)
                    if len(highlight_elements_map) > 0:
                        method.cancel_highlight(dr, highlight_elements_map)
                else:
                    if len(elements) > 0:
                        method.highlight_for_a_moment(dr, elements, 'green')
                    if len(fail_elements) > 0:
                        method.highlight_for_a_moment(dr, fail_elements, 'red')
            except Exception as e:
                e_str = traceback.format_exc()
                ss_name = ''
                logger.error('当前URL为【%s】， 截图出错\n%s' % (last_url, e_str))
                if logger.level < 10:
                    raise
        else:
            logger.info('【%s】\t执行成功' % full_id)
            if is_verify_step:
                try:
                    if get_ss:
                        highlight_elements_map = {}
                        if len(elements) > 0:
                            highlight_elements_map = method.highlight(dr, elements, 'green')
                        ss_name = 'screenshot_{}_{}.png'.format(full_id, uuid.uuid1())
                        ss_name = method.get_current_screenshot(dr=dr, result_dir=result_dir, ss_name=ss_name)
                        if len(highlight_elements_map) > 0:
                            method.cancel_highlight(dr, highlight_elements_map)
                    else:
                        if len(elements) > 0:
                            method.highlight_for_a_moment(dr, elements, 'green')
                except Exception as e:
                    e_str = traceback.format_exc()
                    ss_name = ''
                    logger.error('当前URL为【%s】， 截图出错\n%s' % (last_url, e_str))
                    if logger.level < 10:
                        raise
        step_data_dict['ss_name'] = ss_name
        step_data_dict['last_url'] = last_url
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
    from py_test.general.thread_log import init_logger

    init_logger(log_level=10, console_log_level=20)
    logger = get_thread_logger()
    # base_dir = os.path.dirname(__file__)
    start_time = datetime.datetime.now()
    base_dir = 'D:/vic/debug/TC/test'
    result_dir = 'D:/vic/debug/report'
    # excel_file_name = 'test_oa_ui_1_出差申请_普通用户-全流程.xlsx'
    # excel_file_name = 'test_oa_ui_出差申请_普通用户-发起.xlsx'
    excel_file_name = 'test_ui_2.xlsx'
    excel_file = os.path.join(base_dir, excel_file_name)
    case_result_list = list()
    case_result = run(excel_file=excel_file, tc_id=1, result_dir=result_dir, base_timeout=10, get_ss=0)
    case_result_list.append(case_result)

    end_time = datetime.datetime.now()
    report_title = 'ui_debug'
    report_file_name = 'Automation_Test_Report_' + start_time.strftime("%Y-%m-%d_%H%M%S")
    report_name = vic_method.generate_case_report('ui', result_dir, report_file_name, case_result_list, start_time,
                                                  end_time, report_title)

    logger.info('Report saved as %s' % report_name)
    logger.info('END')
