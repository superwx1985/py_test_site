import json


a = {123: 123, 'aaa': 456}

j = json.dumps(a, indent=1)



print('aaa{}'.format(j))
print('aaa\n'+j)