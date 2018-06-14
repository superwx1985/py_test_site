import json


a = json.dumps(None)

print(a, type(a))

b = json.loads(a)

print(b, type(b))