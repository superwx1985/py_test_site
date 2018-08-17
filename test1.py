import hashlib, uuid, json
from py_test.api_test.method import send_http_request
from py_test.general.vic_method import replace_special_value

a = '${slice|abcd1234,,-8,-1}$'

s = replace_special_value(a, None)



print(s)
