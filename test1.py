import datetime, time
from py_test.general.vic_method import replace_special_value


a = replace_special_value('${{{}|{}}}$'.format('ts', '10.30.2012 20:20:21.456789,%m.%d.%Y %H:%M:%S.%f,,,2,'), None)
a = replace_special_value('${time|1985-10-1}$', None)

print(a, type(a))

