a = '''[{"all":true},{"select_by":"value","select_value":"1"},{"select_by":"text","select_value":"2"},{"select_by":"index","select_value":"3"}]'''

import json

b = json.loads(a)

print(b)

for i in b:
    print(i)
    if 'all' in i:
        print('all')
        if i['all']:
            print('all true')
        else:
            print('all false')
