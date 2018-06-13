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


def execute_step(step, case_result, result_path, step_order, user, variables, level=0, dr=None):
    start_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    logger = get_thread_logger()
    execute_id = '{}-{}'.format(case_result.case_order, step_order)
    logger.info('{}\t执行步骤【{}】'.format(execute_id, step.name))

    # 初始化case result
    step_result = StepResult.objects.create(
        name=step.name,
        description=step.description,
        keyword=step.keyword,
        action=step.action.full_name,
        timeout=step.timeout,
        save_as=step.save_as,
        ui_by=step.ui_by,
        ui_locator=step.ui_locator,
        ui_index=step.ui_index,
        ui_base_element=step.ui_base_element,
        ui_data=step.ui_data,
        ui_special_action=step.ui_special_action,
        ui_alert_handle=step.ui_alert_handle,
        api_url=step.api_url,
        api_headers=step.api_headers,
        api_body=step.api_body,
        api_data=step.api_data,

        case_result=case_result,
        step=step,
        step_order=step_order,
        creator=user,
        start_date=start_date
    )
    step_action = step.action
    try:
        if step_action.type == 'UI':
            if step_action.name == '打开页面':
                if step.ui_data == '':
                    raise ValueError('请提供要打开的URL地址')
            method.go_to_url(dr, step.ui_data)
    except:
        logger.error('{}\t执行出错'.format(execute_id), exc_info=True)

    step_result.end_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    step_result.save()
    return step_result

