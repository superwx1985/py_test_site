import math
import sys
import os





def a():
    print(sys._getframe().f_code.co_name)
    a = get_current_function_name()
    print(a)


a()