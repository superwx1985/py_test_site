import datetime
import json
import logging
import uuid
from py_test.general import vic_variables, vic_public_elements, vic_config, execute_case, vic_log
from concurrent.futures import ThreadPoolExecutor, wait
from py_test.general.vic_method import load_public_data
from main.models import Case, SuiteResult
from django.forms.models import model_to_dict
from utils.system import FORCE_STOP


def execute_suite(suite, user, execute_uuid=uuid.uuid1(), websocket_sender=None):
    # start_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    start_date = datetime.datetime.now()

    logger = logging.getLogger('py_test')
    logger.setLevel(suite.log_level)

    # 设置线程日志level
    vic_log.THREAD_LEVEL = suite.log_level

    # 是否推送websocket
    if websocket_sender:
        logger = vic_log.VicLogger(logger, websocket_sender)

    logger.info('开始')

    # 读取公共变量及元素组
    if suite.variable_group:
        variable_objects = suite.variable_group.variable_set.all()
        global_variables = vic_variables.global_variables  # 初始化全局变量
        public_elements = vic_public_elements.public_elements  # 初始化公共元素组
        load_public_data(variable_objects, global_variables, public_elements)

    # 获取配置
    config = suite.config
    vic_config.set_config(config)

    # 获取用例组
    cases = Case.objects.filter(suite=suite, is_active=True).order_by('suitevscase__order')

    # 限制进程数
    thread_count = suite.thread_count if suite.thread_count <= 10 else 10

    # 初始化suite result
    suite_result = SuiteResult.objects.create(
        name=suite.name,
        description=suite.description,
        keyword=suite.keyword,
        timeout=suite.timeout,
        ui_get_ss=suite.ui_get_ss,
        thread_count=suite.thread_count,
        config=json.dumps(model_to_dict(suite.config)) if suite.config else None,
        variable_group=json.dumps(model_to_dict(suite.variable_group)) if suite.variable_group else None,
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

    if len(cases) == 0:
        logger.info('没有符合条件的用例')
        logger.info('========================================')
        logger.info('结束')
        return suite_result

    logger.info('准备运行下列{}个用例:'.format(len(cases)))
    i = 1
    for case in cases:
        logger.info('【{}】\tID:{} | {}'.format(i, case.pk, case.name))
        i += 1

    logger.info('========================================')
    futures = list()
    pool = ThreadPoolExecutor(thread_count)
    case_order = 0

    for case in cases:
        case_order += 1
        futures.append(pool.submit(
            execute_case.execute_case,
            case=case,
            suite_result=suite_result,
            case_order=case_order,
            user=user,
            execute_str=case_order,
            execute_uuid=execute_uuid,
            websocket_sender=websocket_sender,
        ))

    future_results = wait(futures)
    for future_result in future_results.done:
        case_result = future_result.result()
        suite_result.execute_count += 1
        if case_result.result_status == 1:
            suite_result.pass_count += 1
        elif case_result.result_status == 2:
            suite_result.fail_count += 1
        else:
            suite_result.error_count += 1

    if suite_result.error_count > 0:
        suite_result.result_status = 3
    elif suite_result.fail_count > 0:
        suite_result.result_status = 2
    else:
        suite_result.result_status = 1
    suite_result.end_date = datetime.datetime.now()
    suite_result.save()

    logger.info('测试用例执行完毕')
    logger.info('========================================')
    logger.info('执行: %d | 通过: %d | 失败: %d | 报错: %d' % (
        suite_result.execute_count, suite_result.pass_count, suite_result.fail_count, suite_result.error_count))
    logger.info('耗时: ' + str(suite_result.end_date - suite_result.start_date))
    logger.info('========================================')
    logger.info('结束')

    # 清除停止信号
    if FORCE_STOP.get(execute_uuid):
        del FORCE_STOP[execute_uuid]
    return suite_result


if __name__ == '__main__':
    pass
