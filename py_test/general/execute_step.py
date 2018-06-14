import datetime
import time
import json
import traceback
import pytz
from py_test.general import vic_variables, vic_public_elements, test_result
from py_test.general import vic_method, import_test_data
from py_test.ui_test import method
from selenium.common.exceptions import UnexpectedAlertPresentException, NoSuchElementException
from py_test.vic_tools import vic_eval
from py_test.vic_tools.vic_str_handle import change_digit_to_string, change_string_to_digit
from py_test.general.thread_log import get_thread_logger
from main.models import StepResult, Step
from django.forms.models import model_to_dict

# 获取全局变量
global_variables = vic_variables.global_variables
# 获取公共元素组
public_elements = vic_public_elements.public_elements


def execute_step(step, case_result, result_path, step_order, user, execute_str, variables, parent_case_pk_list,
                 dr=None):
    start_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    logger = get_thread_logger()
    execute_id = '{}-{}'.format(execute_str, step_order)

    # 记录运行的case，防止递归调用
    if parent_case_pk_list is None:
        parent_case_pk_list = [case_result.case.pk]
    else:
        parent_case_pk_list.append(case_result.case.pk)

    # 初始化case result

    step_result = StepResult.objects.create(
        name=step.name,
        description=step.description,
        keyword=step.keyword,
        action=step.action.full_name,

        case_result=case_result,
        step=step,
        step_order=step_order,
        creator=user,
        start_date=start_date,

        step_snapshot=json.dumps(model_to_dict(step)) if step else None,
    )
    try:
        step_action = step.action
        run_result = ('p', 'pass')
        timeout = step.timeout if step.timeout else case_result.suite_result.base_timeout
        save_as = step.save_as
        ui_by_dict = {
            0: '',
            1: 'id',
            2: 'xpath',
            3: 'link text',
            4: 'partial link text',
            5: 'name',
            6: 'tag name',
            7: 'class name',
            8: 'css selector',
            9: 'public element',
            10: 'variable',
        }
        ui_by = ui_by_dict[step.ui_by]
        ui_locator = step.ui_locator
        ui_index = step.ui_index
        ui_base_element = step.ui_base_element
        ui_data = step.ui_data
        ui_special_action = step.ui_special_action
        ui_alert_handle = step.ui_alert_handle

        api_url = step.api_url
        api_headers = step.api_headers
        api_body = step.api_body
        api_data = step.api_data

        other_sub_case = step.other_sub_case

        # ===== UI =====
        # 打开URL
        if step_action.pk == 1:
            if ui_data == '':
                raise ValueError('请提供要打开的URL地址')
            run_result = method.go_to_url(dr, step.ui_data)
        # 输入文字
        elif step_action.pk == 2:
            if ui_by == 0 or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.try_to_enter(dr=dr, by=ui_by, locator=ui_locator, data=ui_data,
                                                       timeout=timeout, index_=ui_index, base_element=ui_base_element,
                                                       variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, elements)


        # ===== API =====
        elif step_action.pk == 0:
            pass

        # ===== DB =====
        elif step_action.pk == 0:
            pass

        # ===== OTHER =====
        elif step_action.pk == 7:
            if step.other_sub_case is None:
                raise ValueError('子用例为空或不存在')
            elif step.other_sub_case.pk in parent_case_pk_list:
                raise ValueError('子用例【{} | {}】不允许递归调用'.format(step.other_sub_case.pk, step.other_sub_case.name))
            else:
                from .execute_case import execute_case
                execute_case(case=step.other_sub_case, suite_result=case_result.suite_result, result_path=result_path,
                             case_order=None, user=user, execute_str=execute_id, variables=variables,
                             step_result=step_result, parent_case_pk_list=parent_case_pk_list, dr=dr)

        else:
            raise ValueError('未知的action')
        if run_result[0] == 'p':
            step_result.result_status = 1
        else:
            step_result.result_status = 2
        step_result.result_message = run_result[1]
    except Exception as e:
        step_result.result_status = 3
        step_result.result_message = str(e)
        step_result.result_error = traceback.format_exc()
        logger.error('{}\t执行出错'.format(execute_id), exc_info=True)

    step_result.end_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    step_result.save()
    return step_result
