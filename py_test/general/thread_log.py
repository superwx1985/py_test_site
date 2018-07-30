import os
import threading
import logging
import logging.config
import logging.handlers
from manage import LOG_DIR

# 子线程日志容器
thread_loggers = dict()

# 日志目录
THREAD_LOG_DIR = os.path.join(LOG_DIR, 'thread_log')
# 检查日志目录是否存在
if not os.path.exists(THREAD_LOG_DIR):
    os.makedirs(THREAD_LOG_DIR)
    print('***** 创建线程日志文件夹 [%s] *****' % THREAD_LOG_DIR)

# 日志级别
THREAD_LEVEL = logging.INFO


# 获取子线程日志
def get_thread_logger(level=None):
    if level is None:
        level = THREAD_LEVEL
    logger_name = threading.current_thread().name
    if logger_name not in thread_loggers:
        thread_logger = logging.getLogger('py_test.{}'.format(logger_name))

        debug_trfh = logging.handlers.RotatingFileHandler(
            filename=os.path.join(THREAD_LOG_DIR, '{}_debug.log'.format(logger_name)), maxBytes=1024*1024*100,
            backupCount=1, encoding='utf-8')
        debug_trfh.setLevel(logging.DEBUG)

        error_trfh = logging.handlers.RotatingFileHandler(
            filename=os.path.join(THREAD_LOG_DIR, '{}_error.log'.format(logger_name)), maxBytes=1024*1024*100,
            backupCount=1, encoding='utf-8')
        error_trfh.setLevel(logging.ERROR)

        thread_logger.addHandler(debug_trfh)
        thread_logger.addHandler(error_trfh)
        thread_logger.setLevel(level)

        thread_loggers[logger_name] = thread_logger
    else:
        thread_logger = thread_loggers[logger_name]
        thread_logger.setLevel(level)
    return thread_logger


# 打印日志时同步推送websocket
class VicLogger:
    def __init__(self, logger, websocket_sender):
        self.logger = logger
        self.websocket_sender = websocket_sender

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
        if self.logger.level < 20:
            self.websocket_sender(msg)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)
        if self.logger.level < 30:
            self.websocket_sender(msg)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)
        if self.logger.level < 40:
            self.websocket_sender(msg)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
        if self.logger.level < 50:
            self.websocket_sender(msg)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)
        self.websocket_sender(msg)
