import logging, json, re
from py_test.vic_tools.vic_find_object import find_with_condition


condition = '''#{json}#["av4"]'''
condition = '''#{json}#{"d-bk":"#{re}#d-bv"}'''
# condition = '''#{json|}#["#{re}#.v."]'''

data = [1, 2, 3, {"d-bk": [1, 2, 3, 'd-bv'], 'bk': 'bv', 'ck': 'cv', 'dk':{'d-bk': 'd-bv'}}]
# data = {"dk": {"d-bk": "d-bv"}}
# data = [1, 2, {"a": [1, 3, 'av']}]
# data = [['av2']]

r = find_with_condition(condition, data)

print(r)
