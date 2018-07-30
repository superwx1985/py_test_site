import datetime
import json
import traceback
import pytz
from py_test.general import vic_variables, vic_public_elements, vic_method, vic_log
from py_test.ui_test import method
from selenium.common.exceptions import UnexpectedAlertPresentException
from main.models import CaseResult, Step
from django.forms.models import model_to_dict
from .execute_step import execute_step


# 获取全局变量
global_variables = vic_variables.global_variables
# 获取公共元素组
public_elements = vic_public_elements.public_elements


def execute_case(
        case, suite_result, case_order, user, execute_str, variables=None, step_result=None, parent_case_pk_list=None,
        dr=None, websocket_sender=None):

    start_date = datetime.datetime.now()
    logger = vic_log.get_thread_logger()
    # 是否推送websocket
    if websocket_sender:
        logger = vic_log.VicLogger(logger, websocket_sender)

    # 初始化case result
    case_result = CaseResult.objects.create(
        name=case.name,
        description=case.description,
        keyword=case.keyword,
        variable_group=json.dumps(model_to_dict(case.variable_group)) if case.variable_group else None,

        suite_result=suite_result,
        step_result=step_result,
        parent_case_pk_list=json.dumps(parent_case_pk_list) if parent_case_pk_list else None,
        case_order=case_order,
        case=case,
        creator=user,
        start_date=start_date,
        execute_count=0,
        pass_count=0,
        fail_count=0,
        error_count=0,
    )

    # 用例初始化
    execute_id = '【{}-{}】'.format(execute_str, 0)
    try:
        logger.info('{}\t初始化用例【{}】'.format(execute_id, case.name))
        config = suite_result.suite.config
        # 初始化driver
        if step_result is None and config.ui_selenium_client != 0:
            dr = method.get_driver(config)

        # 读取测试步骤数据
        steps = Step.objects.filter(case=case, is_active=True).order_by('casevsstep__order').select_related('action')

        # 读取本地变量
        if variables is None:
            variables = vic_variables.Variables()
        local_variable_group = case.variable_group
        if local_variable_group is not None:
            for variable in local_variable_group.variable_set.all():
                value = vic_method.replace_special_value(variable.value, variables)
                variables.set_variable(variable.name, value)

    except Exception as e:
        logger.error('{}\t初始化出错'.format(execute_id), exc_info=True)
        case_result.result_message = '初始化出错：{}'.format(execute_id, getattr(e, 'msg', str(e)))
        case_result.result_error = traceback.format_exc()

    else:
        base_timeout = suite_result.suite.base_timeout
        ui_alert_handle = 'accept'  # 初始化弹窗处理方式
        step_order = 0
        for step in steps:
            step_order += 1
            execute_id = '【{}-{}】'.format(execute_str, step_order)
            logger.info('{}\t执行步骤【{} | {} | {}】'.format(execute_id, step.id, step.name, step.action))

            timeout = step.timeout if not step.timeout else base_timeout

            # 如有弹窗则处理弹窗
            if dr is not None:
                try:
                    _ = dr.current_url
                except UnexpectedAlertPresentException:
                    alert_handle_text, alert_text = method.confirm_alert(dr=dr, alert_handle=ui_alert_handle, timeout=timeout)
                    logger.info('{}\t处理了一个弹窗，处理方式为【{}】，弹窗内容为\n{}'.format(execute_id, alert_handle_text, alert_text))

            step_result_ = execute_step(
                step, case_result, step_order, user, execute_str, variables, parent_case_pk_list, dr=dr, websocket_sender=websocket_sender)

            # 获取最后一次弹窗处理方式
            ui_alert_handle_dict = {
                1: 'accept',
                2: 'dismiss',
                3: 'ignore',
            }
            ui_alert_handle = ui_alert_handle_dict.get(step.ui_alert_handle, 'accept')

            case_result.execute_count += 1
            if step_result_.result_status == 1:
                case_result.pass_count += 1
            elif step_result_.result_status == 2:
                case_result.fail_count += 1
            else:
                case_result.error_count += 1
                break

    # 如果不是子用例，且浏览器未关闭，且logging level大于等于10，则关闭浏览器
    if step_result is None and dr is not None and logger.level >= 10:
        dr.quit()
        del dr

    if case_result.error_count > 0 or case_result.result_error != '':
        case_result.result_status = 3
    elif case_result.fail_count > 0:
        case_result.result_status = 2
        case_result.result_message = '失败'
    else:
        case_result.result_status = 1
        case_result.result_message = '通过'
    case_result.end_date = datetime.datetime.now()
    case_result.save()
    return case_result
