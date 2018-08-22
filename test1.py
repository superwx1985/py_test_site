import hashlib, json
from py_test.api_test.method import send_http_request
from py_test.general.vic_method import replace_special_value

class A:
    name = 'aaaa'

    def method_1(self):
        print(1)

    def method_2(self):
        print(2)

x = A()
for method in dir(x):
    if not method.startswith('__') and callable(getattr(x, method)):
        print(method)


