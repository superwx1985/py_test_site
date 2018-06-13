import logging


class NonWarningFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= 30:
            return False
        return True
