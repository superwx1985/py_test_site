import json
from django.db import connection
from django.db.models import Q, CharField, Value
from django.db.models.functions import Concat
from django.contrib.auth.models import Group
from main.models import Action, Project, Case, Step


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
        q4 = Q()
        for search_text_and in search_text_and_list:
            if search_text_and == '':
                continue
            try:
                int(search_text_and)
                q1 &= Q(pk=search_text_and)
            except ValueError:
                pass
            q2 &= Q(name__icontains=search_text_and)
            q3 &= Q(keyword__icontains=search_text_and)
            # q4 &= Q(project__name__icontains=search_text_and)
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


# 动态获取project
def get_project_list():
    project_list = list()
    project_list.append((None, '---------'))
    project_list.extend(
        list(Project.objects.annotate(pk=Concat('pk', Value(''), output_field=CharField())).values_list('pk', 'name')))
    return project_list


# 验证是否管理员
def check_admin(user):
    try:
        admin_group = Group.objects.get(name='QA_leader')
    except Group.DoesNotExist:
        admin_group = None
    if admin_group in user.groups.all():
        return True
    else:
        return False


# 判断是否存在递归调用
def check_recursive_call(obj, case_list=None):
    if not case_list:
        case_list = list()

    if isinstance(obj, Step) and obj.action.code == 'OTHER_CALL_SUB_CASE' and obj.other_sub_case:
        obj = obj.other_sub_case

    if isinstance(obj, Case):
        if obj.pk in case_list:
            return obj.pk, case_list
        case_list.append(obj.pk)
        print(obj)
        for obj_ in obj.step.all() or []:
            recursive_id, case_list = check_recursive_call(obj_, case_list)
            if recursive_id:
                return recursive_id, case_list
        case_list.pop()

    return None, case_list