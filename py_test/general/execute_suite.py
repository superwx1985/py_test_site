import datetime
import os
import json
import pytz
import logging
from py_test.general import vic_variables, vic_public_elements, vic_config, execute_case
from concurrent.futures import ThreadPoolExecutor, wait
from py_test.general.import_test_data import get_matched_file_list
from py_test.general.vic_method import load_public_data
from main.models import Suite, Case, SuiteResult
from django.forms.models import model_to_dict


def execute_suite(request, pk, result_dir):
    start_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    try:
        suite = Suite.objects.get(pk=pk)
    except Suite.DoesNotExist:
        return

    console_log_level = suite.console_log_level

    logger = logging.getLogger('py_test')
    logger.setLevel(suite.log_level)
    logger.info('开始')
    logger.info(logger.level)
    logger.info('========================================')
    logger.debug('===================debug=====================')
    logger.warning('===================warning=====================')
    start_time = datetime.datetime.now()

    # 读取公共配置
    public_variable_group = suite.variable_group
    global_variables = vic_variables.global_variables  # 初始化全局变量
    public_elements = vic_public_elements.public_elements  # 初始化公共元素组
    load_public_data(public_variable_group, global_variables, public_elements)

    # 获取配置
    config = suite.config
    vic_config.set_config(config)

    # 获取用例组
    cases = Case.objects.filter(suite=suite).order_by('suitevscase__order')

    # 限制进程数
    thread_count = suite.thread_count if suite.thread_count <= 10 else 10

    # 初始化suite result
    suite_result = SuiteResult.objects.create(
        name=suite.name,
        description=suite.description,
        keyword=suite.keyword,
        base_timeout=suite.base_timeout,
        ui_get_ss=suite.ui_get_ss,
        thread_count=suite.thread_count,
        config=json.dumps(model_to_dict(suite.config) if suite.config else {}),
        variable_group=json.dumps(model_to_dict(suite.variable_group) if suite.variable_group else {}),

        suite=suite,
        creator=request.user,
        start_date=start_date
    )

    if len(cases) == 0:
        logger.info('没有符合条件的用例')
        logger.info('========================================')
        logger.info('结束')
        return '', 0, 0, 0, 0, 0

    report_folder_name = 'Automation_Test_Report_' + start_time.strftime("%Y-%m-%d_%H%M%S")
    result_path = os.path.join(result_dir, report_folder_name)
    if not os.path.isabs(result_path):  # 如果报告路径不是绝对路径，则生成在工程文件夹
        result_path = os.path.join(os.getcwd(), result_path)
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    logger.info('准备运行下列【%s】个用例:' % len(cases))
    i = 1
    for case in cases:
        logger.info('%s.\t%s' % (i, case.name))
        i += 1

    futures = list()
    pool = ThreadPoolExecutor(thread_count)
    case_order = 0

    for case in cases:
        futures.append(pool.submit(
            execute_case.execute_case,
            case=case,
            suite_result=suite_result,
            result_path=result_path,
            case_order=case_order,
            user=request.user,
        ))
        case_order += 1

    future_results = wait(futures)
    case_result_list = list()
    all_case_count = 0
    pass_case_count = 0
    fail_case_count = 0
    error_case_count = 0
    skip_case_count = 0
    for future_result in future_results.done:
        case_result = future_result.result()
        print(case_result)
    # for future_result in future_results.done:
    #     case_result = future_result.result()
    #     case_result_list.append(case_result)
    #     all_case_count += 1
    #     if case_result.status == 'p':
    #         pass_case_count += 1
    #     elif case_result.status == 'f':
    #         fail_case_count += 1
    #     elif case_result.status == 'e':
    #         error_case_count += 1
    #     else:
    #         skip_case_count += 1

    # 按case id排序
    case_result_list.sort(key=lambda x: x.id)

    end_time = datetime.datetime.now()
    elapsed_time = end_time - start_time
    logger.info('测试用例执行完毕')
    logger.info('========================================')
    logger.info('执行: %d, 通过: %d, 失败: %d, 报错: %d, 跳过: %d' % (
        all_case_count, pass_case_count, fail_case_count, error_case_count, skip_case_count))
    logger.info('耗时: ' + str(elapsed_time))
    logger.info('========================================')
    logger.info('开始生成测试报告...')

    from py_test.general.vic_method import generate_case_report
    # report_name = generate_case_report(case_type=case_type, result_dir=result_path, report_file_name=report_folder_name,
    #                                    case_result_list=case_result_list, start_time=start_time, end_time=end_time,
    #                                    report_title=report_title)
    report_name = case_order

    logger.info('测试报告生成完毕 => %s' % report_name)
    logger.info('========================================')
    logger.info('结束')

    suite_result.end_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    suite_result.save()
    return suite_result


if __name__ == '__main__':
    pass
