import json
from django.db import connection
from django.db.models import Q
from main.models import Action


class Cookie:
    def __init__(self, key, value, max_age=None, expires=None, path='/'):
        self.key = key
        self.value = value
        self.max_age = max_age
        self.expires = expires
        self.path = path


# 生成查询条件的Q对象
def get_query_condition(search_text):
    search_text = search_text.replace('\\ ', '#{$blank}#')
    search_text_or_list = search_text.split(' ')

    q = Q()
    for search_text_or in search_text_or_list:
        search_text_or = search_text_or.replace('#{$blank}#', ' ')
        search_text_and_list = search_text_or.split('#&&#')
        q1 = Q()
        q2 = Q()
        q3 = Q()
        for search_text_and in search_text_and_list:
            if search_text_and == '':
                continue
            q1 &= Q(name__icontains=search_text_and)
            q2 &= Q(keyword__icontains=search_text_and)
            q3 &= Q(project__name__icontains=search_text_and)
        q |= q1 | q2 | q3
    return q


# 把字符串转为正整数
def change_to_positive_integer(value, default=1):
    if str(value).isdigit() and int(value) > 0:
        value = int(value)
    else:
        value = default
    return value


# 执行sql
def execute_query(sql):
    cursor = connection.cursor()  # 获得一个游标(cursor)对象
    cursor.execute(sql)
    raw_data = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    result = list()
    for row in raw_data:
        obj_dict = dict()
        # 把每一行的数据遍历出来放到Dict中
        for index, value in enumerate(row):
            obj_dict[col_names[index]] = value
        result.append(obj_dict)
    return result


# 获取action pk和code的映射关系
def get_action_map_json():
    action_map = dict()
    for action_obj in Action.objects.values('pk', 'code'):
        action_map[action_obj['pk']] = action_obj['code']
    return json.dumps(action_map)