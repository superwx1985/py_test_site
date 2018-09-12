import logging


# 日志级别
THREAD_LEVEL = logging.INFO


# 日志格式
format_standard = logging.Formatter('%(asctime)s [%(threadName)s:%(thread)d] [%(name)s] [%(module)s:%(funcName)s:%(lineno)d] [%(levelname)s] - %(message)s')
format_detail = logging.Formatter('%(asctime)s [%(threadName)s:%(thread)d] [%(name)s] [%(pathname)s:%(funcName)s:%(lineno)d] [%(levelname)s] - %(message)s')


# 推送日志到websocket
class WebsocketHandler(logging.Handler):
    def __init__(self, ws_sender):
        self.ws_sender = ws_sender
        super().__init__()

    def emit(self, record):
        try:
            msg = self.format(record)
            self.ws_sender(msg, record.levelno)
        except Exception:
            self.handleError(record)
