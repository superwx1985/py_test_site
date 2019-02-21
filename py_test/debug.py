# from py_test.general import vic_method
#
# a = vic_method.replace_special_value('${t|2000-10-1,,,,date}$')
# print(a)
# a = vic_method.replace_special_value('${t|2000-08-11 09:23:40,,second,3,S}$')
# print(a)


# from py_test.vic_tools.vic_eval import EvalObject
#
# eo = EvalObject('admin', variable_dict={'x': 1})
#
# print(eo.get_eval_result())

import threading
import time

now_time = time.time()

print(now_time)