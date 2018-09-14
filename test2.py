import datetime, time, logging
from py_test.general.vic_method import replace_special_value


a = replace_special_value('${{{}|{}}}$'.format('r', '50,100,2'), None, None, logger=logging.getLogger('debug'))

print(a, type(a))