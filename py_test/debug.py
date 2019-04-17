# from py_test.general import vic_method

# a = vic_method.replace_special_value('${t|2000-10-1,,,,date}$')
# print(a)
# a = vic_method.replace_special_value('${t|2020-02-29 11:12:13.1123,,year,-1,full}$')
# print(a)


# from py_test.vic_tools.vic_eval import EvalObject
#
# eo = EvalObject('admin', variable_dict={'x': 1})
#
# print(eo.get_eval_result())


from py_test.vic_tools.vic_find_object import find_with_condition, FindObject
from py_test.general import vic_log
import json
import logging
logger = logging.getLogger('debug')
logger.setLevel(10)
sh = logging.StreamHandler()
sh.setLevel(10)
sh.setFormatter(vic_log.format_standard)
logger.addHandler(sh)

j1 = '#{json}#{"b": "#{json|l}#[1, 2, \\"#{json}#[4, 5, \\"#{json|l}#[5,5]\\"]\\"]"}'
j1 = '#{json}#{"b": "#{json|l}#[1, 2, \\"#{json}#[4, 5, \\\\"#{json|l}#[5,5]\\\\"]\\"]"}'
o2 = {"a": "a1", "b": [1, 2, ["abc", 4, 5, [5, 5]]], "c": {"1": 1, "2": 2}}
j2 = json.dumps(o2)


r = find_with_condition(j1, j2, logger=logger)
print(r)
