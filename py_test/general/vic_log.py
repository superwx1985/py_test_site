import os
import uuid
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


# 日志格式
format_standard = logging.Formatter('%(asctime)s [%(threadName)s:%(thread)d] [%(name)s] [%(module)s:%(funcName)s:%(lineno)d] [%(levelname)s] - %(message)s')
format_detail = logging.Formatter('%(asctime)s [%(threadName)s:%(thread)d] [%(name)s] [%(pathname)s:%(funcName)s:%(lineno)d] [%(levelname)s] - %(message)s')


# 获取子线程日志
def get_thread_logger(execute_uuid=uuid.uuid1(), level=None):
    if level is None:
        level = THREAD_LEVEL
    thread_name = threading.current_thread().name
    thread_logger = logging.getLogger('py_test.{}.{}'.format(execute_uuid, thread_name))
    debug_trfh = logging.handlers.RotatingFileHandler(
        filename=os.path.join(THREAD_LOG_DIR, '{}_debug.log'.format(thread_name)), maxBytes=1024*1024*100,
        backupCount=1, encoding='utf-8')
    debug_trfh.setLevel(logging.DEBUG)
    debug_trfh.setFormatter(format_detail)

    error_trfh = logging.handlers.RotatingFileHandler(
        filename=os.path.join(THREAD_LOG_DIR, '{}_error.log'.format(thread_name)), maxBytes=1024*1024*100,
        backupCount=1, encoding='utf-8')
    error_trfh.setLevel(logging.ERROR)
    error_trfh.setFormatter(format_detail)

    thread_logger.addHandler(debug_trfh)
    thread_logger.addHandler(error_trfh)
    thread_logger.setLevel(level)

    # if thread_name not in thread_loggers:
    #     thread_logger = logging.getLogger('py_test.{}.{}'.format(execute_uuid, thread_name))
    #
    #     debug_trfh = logging.handlers.RotatingFileHandler(
    #         filename=os.path.join(THREAD_LOG_DIR, '{}_debug.log'.format(thread_name)), maxBytes=1024*1024*100,
    #         backupCount=1, encoding='utf-8')
    #     debug_trfh.setLevel(logging.DEBUG)
    #     debug_trfh.setFormatter(format_detail)
    #
    #     error_trfh = logging.handlers.RotatingFileHandler(
    #         filename=os.path.join(THREAD_LOG_DIR, '{}_error.log'.format(thread_name)), maxBytes=1024*1024*100,
    #         backupCount=1, encoding='utf-8')
    #     error_trfh.setLevel(logging.ERROR)
    #     error_trfh.setFormatter(format_detail)
    #
    #     thread_logger.addHandler(debug_trfh)
    #     thread_logger.addHandler(error_trfh)
    #     thread_logger.setLevel(level)
    #
    #     thread_loggers[thread_name] = thread_logger
    # else:
    #     thread_logger = thread_loggers[thread_name]
    #     thread_logger.setLevel(level)
    return thread_logger


# 推送日志到websocket
class WebsocketHandler(logging.Handler):
    def __init__(self, ws_sender):
        self.ws_sender = ws_sender
        super().__init__()
        # logging.Handler.__init__(self)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.ws_sender(msg, record.levelno)
        except Exception:
            self.handleError(record)
