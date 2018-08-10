import hashlib, uuid, json
from py_test.api_test.method import send_http_request
import httplib2

url = 'http://127.0.0.1:8000/debug3/'

# response, str_content, response_start_time, response_end_time = send_http_request(url=url)
# print(str_content)


h = httplib2.Http(timeout=10)

response, content = h.request(uri=url, method='GET')

print(response)
print(content)

str_content = content.decode('GB2312')
# str_content = str(content)

print(str_content)

j = json.loads(str_content)

print(j['data'])