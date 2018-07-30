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
