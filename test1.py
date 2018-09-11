import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
import re
from py_test.vic_tools import vic_find_object


condition_value = '#{re}#value="(.*?)".*(\\1)'
data = 'value="111" sdad 111 value="222" 222'

re_parameter = []
result = vic_find_object.find_with_condition(condition_value, data)
print(result.re_result)
