import datetime, time, logging
from py_test.general.vic_method import replace_special_value

str = '${t|2018-09-26 09:28:15.956083,,,,yd}$'
a = replace_special_value('${{{}|{}}}$'.format('r', '50,100,2'), None, None, logger=logging.getLogger('debug'))
a = replace_special_value(str, None, None, logger=logging.getLogger('debug'))

print(a, type(a))