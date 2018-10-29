import datetime
import json
import logging
import uuid
# import pytz
from py_test.general import vic_variables, vic_public_elements, vic_config, vic_log, vic_method
from .vic_case import VicCase
from concurrent.futures import ThreadPoolExecutor, wait
from main.models import Case, SuiteResult, Step
from django.forms.models import model_to_dict
from utils.system import FORCE_STOP


def execute_suite(suite, user, execute_uuid=uuid.uuid1(), websocket_sender=None):
    start_date = datetime.datetime.now()

    logger = logging.getLogger('py_test.{}'.format(execute_uuid))
    logger.setLevel(suite.log_level)

    # 设置线程日志level
    vic_log.THREAD_LEVEL = suite.log_level

    # 是否推送websocket
    if websocket_sender:
        date_fmt = '%H:%M:%S'
        format_ = logging.Formatter('%(asctime)s [%(threadName)s] - %(message)s', date_fmt)
        ws_handler = vic_log.WebsocketHandler(websocket_sender)
        ws_handler.setFormatter(format_)
        logger.addHandler(ws_handler)

    logger.info('开始')

    # 初始化全局变量
    global_variables = vic_variables.Variables(logger)
    if suite.variable_group:
        variable_objects = suite.variable_group.variable_set.all()
        for obj in variable_objects:
            value = vic_method.replace_special_value(obj.value, global_variables, None, logger)
            global_variables.set_variable(obj.name, value)

    # 初始化公共元素组
    public_elements = vic_public_elements.PublicElements(logger)
    if suite.element_group:
        element_objects = suite.element_group.element_set.all()
        # 获取by映射
        ui_by_dict = {i[0]: i[1] for i in Step.ui_by_list}
        for obj in element_objects:
            ui_by = ui_by_dict[obj.by]
            public_elements.add_element_info(obj.name, (ui_by, obj.locator))

    # 获取配置
    config = suite.config
    vic_config.set_config(config)

    # 限制进程数
    thread_count = suite.thread_count if suite.thread_count <= 10 else 10

    # 获取变量组json
    if suite.variable_group:
        v_list = list(suite.variable_group.variable_set.all().values('pk', 'name', 'description', 'value', 'order'))
        variable_group_dict = model_to_dict(suite.variable_group)
        variable_group_dict['variables'] = v_list
        variable_group_json = json.dumps(variable_group_dict)
    else:
        variable_group_json = None

    # 获取元素组json
    if suite.element_group:
        v_list = list(suite.element_group.element_set.all().values('pk', 'name', 'description', 'by', 'locator', 'order'))
        element_group_dict = model_to_dict(suite.element_group)
        element_group_dict['element'] = v_list
        element_group_json = json.dumps(element_group_dict)
    else:
        element_group_json = None

    # 初始化suite result
    suite_result = SuiteResult.objects.create(
        name=suite.name,
        description=suite.description,
        keyword=suite.keyword,
        timeout=suite.timeout,
        ui_get_ss=suite.ui_get_ss,
        thread_count=suite.thread_count,
        config=json.dumps(model_to_dict(suite.config)) if suite.config else None,
        variable_group=variable_group_json,
        element_group=element_group_json,
        project=suite.project,

        suite=suite,
        creator=user,
        modifier=user,
        start_date=start_date,

        execute_count=0,
        pass_count=0,
        fail_count=0,
        error_count=0,
    )

    # 获取用例组
    cases = Case.objects.filter(suite=suite, is_active=True).order_by('suitevscase__order')
    if len(cases) == 0:
        logger.info('没有符合条件的用例')
        logger.info('========================================')
        logger.info('结束')
        return suite_result

    logger.info('准备运行下列{}个用例:'.format(len(cases)))
    vic_cases = list()
    case_order = 0
    for case in cases:
        case_order += 1
        vic_cases.append(
            VicCase(
                case=case, suite_result=suite_result, case_order=case_order, user=user, execute_str=case_order,
                execute_uuid=execute_uuid, websocket_sender=websocket_sender)
        )
        logger.info('【{}】\tID:{} | {}'.format(case_order, case.pk, case.name))

    logger.info('========================================')
    futures = list()
    pool = ThreadPoolExecutor(thread_count)

    case_order = 0
    for case in vic_cases:
        case_order += 1
        futures.append(pool.submit(case.execute, global_variables, public_elements))

    future_results = wait(futures)
    for future_result in future_results.done:
        case_result = future_result.result()
        suite_result.execute_count += 1
        if case_result.result_status == 1:
            suite_result.pass_count += 1
        elif case_result.result_status == 2:
            suite_result.fail_count += 1
        elif case_result.result_status == 3:
            suite_result.error_count += 1

    skip_count = suite_result.execute_count - suite_result.pass_count - suite_result.fail_count - suite_result.error_count

    if suite_result.error_count > 0:
        suite_result.result_status = 3
    elif suite_result.fail_count > 0:
        suite_result.result_status = 2
    elif suite_result.execute_count == skip_count:
        suite_result.result_status = 0
    else:
        suite_result.result_status = 1
    suite_result.end_date = datetime.datetime.now()
    suite_result.save()

    logger.info('测试用例执行完毕')
    logger.info('========================================')
    logger.info('执行: %d | 通过: %d | 失败: %d | 出错: %d | 跳过: %d' % (
        suite_result.execute_count, suite_result.pass_count, suite_result.fail_count, suite_result.error_count,
        skip_count))
    logger.info('耗时: ' + str(suite_result.end_date - suite_result.start_date))
    logger.info('========================================')
    logger.info('结束')

    # 清除停止信号
    if FORCE_STOP.get(execute_uuid):
        del FORCE_STOP[execute_uuid]

    # 关闭日志文件句柄
    for h in logger.handlers:
        h.close()

    return suite_result


if __name__ == '__main__':
    pass
