from py_test.general.run_case_group import batch_run_excel


def run(public_file_dir, case_dir, result_dir, case_type, base_timeout, get_ss, log_level, console_log_level,
        thread_count):
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
    report_name, all_case_count, pass_case_count, fail_case_count, error_case_count, skip_case_count = batch_run_excel(
        public_file_dir=public_file_dir, case_dir=case_dir, case_ignore=case_ignore, case_prefix=case_prefix,
        case_suffix=case_suffix, case_keyword=case_keyword, result_dir=result_dir, case_type=case_type,
        base_timeout=base_timeout, report_title='自动化测试报告', get_ss=get_ss, log_level=log_level,
        console_log_level=console_log_level, thread_count=thread_count)
    if fail_case_count > 0 or error_case_count > 0:
        raise AssertionError('本次测试未通过，请查看测试报告 => {}'.format(report_name))


if __name__ == '__main__':
    from sys import argv

    # 需要N个参数
    n = 9
    msg = '''只接收到{}个参数。请提供{}个参数，依次是：
1.公共配置目录
2.用例目录
3.结果目录
4.用例类型
5.基础超时值
6.是否截图
7.日志级别
8.控制台日志级别
9.线程数'''
    if len(argv) < n + 1:
        raise ValueError(msg.format(len(argv) - 1, n))
    public_file_dir = argv[1]
    case_dir = argv[2]
    result_dir = argv[3]
    case_type = argv[4]
    base_timeout = float(argv[5])
    get_ss = int(argv[6])
    log_level = int(argv[7])
    console_log_level = int(argv[8])
    thread_count = int(argv[9])
    run(public_file_dir, case_dir, result_dir, case_type, base_timeout, get_ss, log_level, console_log_level,
        thread_count)
