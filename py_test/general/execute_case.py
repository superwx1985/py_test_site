import datetime
import time
import json
import traceback
import pytz
from py_test.general import vic_variables, vic_public_elements
from py_test.general import vic_method
from py_test.ui_test import method
from selenium.common.exceptions import UnexpectedAlertPresentException
from py_test.general.thread_log import get_thread_logger
from main.models import CaseResult, Step
from django.forms.models import model_to_dict
from .execute_step import execute_step


# 获取全局变量
global_variables = vic_variables.global_variables
# 获取公共元素组
public_elements = vic_public_elements.public_elements


def execute_case(case, suite_result, result_path, case_order, user, variables=None, step_result=None, level=0, dr=None):
    start_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    logger = get_thread_logger()
    # 创建截图保存目录
    # if result_dir == None:
    #     result_dir = project_dir
    # if not os.path.exists(result_dir):
    #     # 防止多线程运行时，创建同名文件夹报错
    #     try:
    #         os.makedirs(result_dir)
    #     except FileExistsError:
    #         pass

    # 初始化case result
    case_result = CaseResult.objects.create(
        name=case.name,
        description=case.description,
        keyword=case.keyword,
        variable_group=json.dumps(model_to_dict(case.variable_group) if case.variable_group else {}),

        suite_result=suite_result,
        step_result=step_result,
        level=level,
        case_order=case_order,
        case=case,
        creator=user,
        start_date=start_date
    )

    # 用例初始化
    try:
        execute_id = '{}-{}'.format(case_order, 0)
        logger.info('{}\t初始化用例【{}】'.format(execute_id, case.name))
        config = suite_result.suite.config
        # 初始化driver
        if level == 0 and config.ui_selenium_client != 0:
            dr = method.get_driver(config)

        # 读取测试步骤数据
        steps = Step.objects.filter(case=case).order_by('casevsstep__order').select_related('action')

        # 读取本地变量
        if variables is None:
            variables = vic_variables.Variables()
        local_variable_group = case.variable_group
        if local_variable_group is not None:
            for variable in local_variable_group.variable_set.all():
                value = vic_method.replace_special_value(variable.value, variables)
                variables.set_variable(variable.name, value)

    except Exception as e:
        logger.error('{}-{}\t初始化出错'.format(case_order, 0), exc_info=True)
        suite_result.end_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        suite_result.save()
        if logger.level < 10:
            raise
        return suite_result

    base_timeout = suite_result.suite.base_timeout
    ui_get_ss = suite_result.suite.ui_get_ss
    last_alert_handle = ''  # 初始化弹窗处理方式
    step_order = 0
    for step in steps:
        step_order += 1
        logger.info('{}-{}\t{}|{}'.format(case_order, step_order, step.name, step.action))

        timeout = step.timeout if not step.timeout else base_timeout

        alert_handle = last_alert_handle
        # 如有弹窗则处理弹窗
        if dr is not None:
            try:
                last_url = dr.current_url
            except UnexpectedAlertPresentException:
                alert_handle_text, alert_text = method.confirm_alert(dr=dr, alert_handle=alert_handle, timeout=timeout)
                logger.info('{}-{}\t处理了一个弹窗，处理方式为【{}】，弹窗内容为\n{}'.format(case_order, step_order, alert_handle_text, alert_text))
            if last_url == 'data:,':
                last_url = ''

        step_result = execute_step(step, case_result, result_path, step_order, user, variables, level=level, dr=dr)
        print(step_result.pk)

    if level == 0 and dr is not None:
        dr.quit()
        dr = None

    time.sleep(3)
    case_result.end_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    case_result.save()
    return case_result
