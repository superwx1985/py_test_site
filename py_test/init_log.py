import os
import threading
import logging
import logging.config
import logging.handlers


# 读取日志配置文件
def load_log_conf(log_conf):
    while True:
        try:
            logging.config.fileConfig(log_conf, {})
        except FileNotFoundError as e:
            # 如果日志文件夹不存在则创建该文件夹
            file_dir = os.path.dirname(e.filename)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                print('***** 创建日志文件夹 [%s] *****' % file_dir)
            continue
        else:
            return logging.getLogger('py_test')


# 获取工程根目录
project_dir = os.path.dirname(os.path.abspath(__file__))
# 日志目录
log_dir = os.path.join(project_dir, 'log')
# 检查日志目录是否存在
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    print('***** 创建日志文件夹 [%s] *****' % log_dir)
# 子线程日志容器
thread_loggers = dict()
# 全局日志参数容器
log_para = dict()
log_para['level'] = 10


# 初始化日志
def init_logger(log_level=logging.INFO, console_log_level=logging.INFO):

    simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s: %(message)s')

    from sys import stdout
    ch = logging.StreamHandler(stdout)
    ch.setLevel(console_log_level)
    ch.setFormatter(simple_formatter)

    logger = logging.getLogger('py_test')
    logger.setLevel(log_level)
    log_para['level'] = log_level
    logger.addHandler(ch)


# 获取子线程日志
def get_thread_logger():
    logger_name = threading.current_thread().name
    if logger_name not in thread_loggers:
        thread_logger = logging.getLogger('py_test.{}'.format(logger_name))

        full_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(pathname)s - %(funcName)s - %(lineno)s: %(message)s')
        debug_trfh = logging.handlers.TimedRotatingFileHandler(
            filename=os.path.join(log_dir, '{}_debug.log'.format(logger_name)), when='h', interval=1,
            backupCount=24 * 7, encoding='utf-8')
        debug_trfh.setLevel(logging.DEBUG)
        debug_trfh.setFormatter(full_formatter)

        error_trfh = logging.handlers.TimedRotatingFileHandler(
            filename=os.path.join(log_dir, '{}_error.log'.format(logger_name)), when='d', interval=1, backupCount=30,
            encoding='utf-8')
        error_trfh.setLevel(logging.ERROR)
        error_trfh.setFormatter(full_formatter)

        thread_logger.addHandler(debug_trfh)
        thread_logger.addHandler(error_trfh)
        thread_logger.setLevel(log_para['level'])

        thread_loggers[logger_name] = thread_logger
    else:
        thread_logger = thread_loggers[logger_name]
    return thread_logger
