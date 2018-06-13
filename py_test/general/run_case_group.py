import datetime
import os
import logging
from py_test.general import vic_variables, vic_public_elements
from concurrent.futures import ThreadPoolExecutor, wait
from py_test.general.import_test_data import get_matched_file_list
from py_test.general.vic_method import load_public_data


def get_public_file_list(public_file_dir):
    public_file_list = list()
    file_list = get_matched_file_list(_dir=public_file_dir, ignore='~$', prefix='', suffix='xls,xlsx', keyword='')
    for file in file_list:
        public_file_list.append(os.path.join(public_file_dir, file))
    return public_file_list


def get_case_list(case_dir, case_ignore, case_prefix, case_suffix, case_keyword):
    tcs = list()
    file_list = get_matched_file_list(case_dir, case_ignore, case_prefix, case_suffix, case_keyword)
    for file in file_list:
        tcs.append((os.path.join(case_dir, file), file))
    return tcs


def batch_run_excel(public_file_dir, case_dir, case_ignore, case_prefix, case_suffix, case_keyword, result_dir,
                    case_type, base_timeout=30, report_title='自动化测试报告', get_ss=True, log_level=logging.DEBUG,
                    console_log_level=logging.INFO, thread_count=1):
    from py_test.general.thread_log import init_logger, get_thread_logger
    init_logger(log_level, console_log_level)
    logger = get_thread_logger()
    logger.info('开始')
    logger.info('========================================')
    start_time = datetime.datetime.now()
    case_type_mapping = {
        'api': 'api',
        'a': 'api',
        'selenium': 'ui',
        's': 'ui',
        'ui': 'ui',
        'database': 'db',
        'db': 'db',
    }
    if case_type not in case_type_mapping:
        raise ValueError('无效的用例类型【%s】' % case_type)

    # 读取公共配置
    public_file_list = get_public_file_list(public_file_dir)
    global_variables = vic_variables.global_variables  # 初始化全局变量
    public_elements = vic_public_elements.public_elements  # 初始化公共元素组
    load_public_data(public_file_list, global_variables, public_elements)

    tcs = get_case_list(case_dir, case_ignore, case_prefix, case_suffix, case_keyword)
    if len(tcs) == 0:
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

    logger.info('准备运行下列【%s】个用例:' % len(tcs))
    i = 1
    for tc in tcs:
        logger.info('%s.\t%s' % (i, tc[1]))
        i += 1

    futures = list()
    pool = ThreadPoolExecutor(thread_count)
    tc_id = 1
    for tc in tcs:
        if case_type_mapping[case_type] == 'ui':
            from py_test.ui_test.run_case import run
            futures.append(
                pool.submit(run, excel_file=tc[0], tc_id=tc_id, variables=vic_variables.Variables(),
                            result_dir=result_path, base_timeout=base_timeout, get_ss=get_ss))
        elif case_type_mapping[case_type] == 'api':
            from py_test.api_test import run
            futures.append(
                pool.submit(run, excel_file=tc[0], tc_id=tc_id, variables=vic_variables.Variables(),
                            result_dir=result_path, base_timeout=base_timeout))
        elif case_type_mapping[case_type] == 'db':
            from py_test.db_test import run
            futures.append(pool.submit(run, excel_file=tc[0], tc_id=tc_id, variables=vic_variables.Variables()))
        tc_id += 1

    future_results = wait(futures)
    case_result_list = list()
    all_case_count = 0
    pass_case_count = 0
    fail_case_count = 0
    error_case_count = 0
    skip_case_count = 0
    for future_result in future_results.done:
        case_result = future_result.result()
        case_result_list.append(case_result)
        all_case_count += 1
        if case_result.status == 'p':
            pass_case_count += 1
        elif case_result.status == 'f':
            fail_case_count += 1
        elif case_result.status == 'e':
            error_case_count += 1
        else:
            skip_case_count += 1

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
    report_name = generate_case_report(case_type=case_type, result_dir=result_path, report_file_name=report_folder_name,
                                       case_result_list=case_result_list, start_time=start_time, end_time=end_time,
                                       report_title=report_title)
    logger.info('测试报告生成完毕 => %s' % report_name)
    logger.info('========================================')
    logger.info('结束')
    return report_name, all_case_count, pass_case_count, fail_case_count, error_case_count, skip_case_count


if __name__ == '__main__':
    # base_dir = os.path.dirname(__file__)
    public_file_dir = 'D:/自动化测试工具/test_case/public'
    case_dir = 'D:/自动化测试工具/test_case/ui'
    case_ignore = '''
~$
'''
    case_prefix = '''

'''
    case_suffix = '''
xls, xlsx
'''
    case_keyword = '''

'''
    result_dir = 'D:/自动化测试工具/report'

    batch_run_excel(public_file_dir, case_dir, case_ignore, case_prefix, case_suffix, case_keyword, result_dir,
                    case_type='ui', base_timeout=10, report_title='debug', get_ss=1, log_level=5,
                    console_log_level=logging.INFO, thread_count=1)

    # 报告上传ftp
    # hostaddr = '192.168.119.23'  # ftp地址
    # username = 'wangx'  # 用户名
    # password = '123456'  # 密码
    # port = 9921  # 端口号
    # encoding = 'gbk'  # 设置字符编码
    # rootdir_local = os.path.split(reportname)[0]  # 本地目录
    # rootdir_remote = '/result/'  # 远程目录
    # import vic_test.vic_FTP as vic_FTP
    # f = vic_FTP.MYFTP(hostaddr, username, password, rootdir_remote, port, encoding)
    # f.login()
    # f.download_files(rootdir_local, rootdir_remote)
    # f.upload_files(rootdir_local, rootdir_remote, 1)
