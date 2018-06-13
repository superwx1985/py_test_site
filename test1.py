import sys
import logging
import logging.handlers


def non_warning_filter(message):
    if message.levelno >= 30:
        return False
    return True


logger = logging.getLogger('1')

err = logging.StreamHandler(sys.stderr)
err.setLevel(logging.WARNING)
out = logging.StreamHandler(sys.stdout)
out.setLevel(logging.DEBUG)
out.addFilter(non_warning_filter)

logger.addHandler(err)
logger.addHandler(out)

logger.setLevel(logging.DEBUG)

logger.critical('critical')
logger.error('error')
logger.warning('warning')
logger.info('info')
logger.debug('debug')
