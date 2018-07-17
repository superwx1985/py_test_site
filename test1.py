import hashlib, uuid, json

l = list()
for i in range(1, 101):
    d = dict()
    d['id'] = 'test{:0>4d}'.format(i)
    u = uuid.uuid1()
    d['key3'] = str(u).replace('-', '')[0:16]

    hl = hashlib.md5()
    hl.update(str(u).encode(encoding='utf-8'))
    d['key2'] = hl.hexdigest()
    print(d)
    l.append(d)


j = json.dumps(l, indent=4)
print(j)
