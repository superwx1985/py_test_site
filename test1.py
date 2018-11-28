from py_test.general import vic_method
from py_test.vic_tools import vic_find_object
import argparse
import sys

a = None

for x in a or []:
    print(x)
