import logging
import json
from py_test.api_test.method import send_http_request


headers = {"Content-Type": "application/x-www-form-urlencoded", "Cookie": "csrftoken=bWAWImSgDrqudx28zevfT3qKIF2pbQww0PLhQjR0lkkfGlRpJvtKuptULOOVsnjy"}

headers = json.dumps(headers)

body = 'csrfmiddlewaretoken=xUMPm7Fccxb14oTtS2KUWNl4daoRVAgFmNXau4EWUq5MxcIK2jIpx9oegjanc73H&username=vic&password=abcd123%21'


a = send_http_request('http://192.192.185.140/user/login/', method='POST', headers=headers, body=body, timeout=30, logger=logging.getLogger('py_test'))

print(a[0])
print(a[1][:1000])

headers = {"Cookie": a[0]['set-cookie']}

headers = json.dumps(headers)

body = 'csrfmiddlewaretoken=xUMPm7Fccxb14oTtS2KUWNl4daoRVAgFmNXau4EWUq5MxcIK2jIpx9oegjanc73H&username=vic&password=abcd123%21'


a = send_http_request('http://192.192.185.140/home/', method='GET', headers=headers, body=body, timeout=30, logger=logging.getLogger('py_test'))

print(a[0])
print(a[1][:1000])
