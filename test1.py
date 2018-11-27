from py_test.general import vic_method
from py_test.vic_tools import vic_find_object
import argparse
import sys


class C1:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '[I am c1, my name is {}]'.format(self.name)


class C2:
    c1 = None

    def __str__(self):
        return '[I am c2, my c1 is {}]'.format(self.c1.__str__())


c1_1 = C1(1)
c1_2 = C1(2)
c1_3 = C1(3)

c2_1 = C2()
c2_1.c1 = c1_1

d = dict()

d[c2_1.c1] = c2_1.c1
d[c1_2] = c1_2

print(c2_1)
for k, v in d.items():
    print(k, '******', v)

print('========================')
d[c2_1.c1] = c1_3
c2_1.c1 = c1_3
print(c2_1)
for k, v in d.items():
    print(k, '******', v)

print(d.get(c2_1.c1))
