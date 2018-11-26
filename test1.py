from py_test.general import vic_method
from py_test.vic_tools import vic_find_object
import argparse
import sys

def get_first_str_in_re_result(re_result):
    if re_result:
        if isinstance(re_result, (list, tuple)):
            for result_ in re_result:
                if result_:
                    if isinstance(result_, (list, tuple)):
                        for result__ in result_:
                            if result__:
                                return str(result__)
                    else:
                        return str(result_)
        else:
            return str(re_result)
    return None
s = '#{re}#tid=(.*)&|tid=(.*)$'
data = 'cid=123&tid=456'


r = vic_find_object.find_with_condition(s, data)

print(r)
print(get_first_str_in_re_result(r.re_result))



