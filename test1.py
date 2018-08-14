import hashlib, uuid, json
from py_test.api_test.method import send_http_request
import httplib2

a = '123'

b = []

[b.append(str(i)) for i in range(len(a))]


s = '|'.join(b)

print(s)