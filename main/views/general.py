from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db import connection
from django.db.models import Q
from django.contrib import auth
from django.contrib.auth.decorators import login_required


# 生成查询条件的Q对象
def get_query_condition(query_str_list):
    q = Q()
    for query_str in query_str_list:
        query_str = str(query_str)
        q |= Q(name__icontains=query_str) | Q(keyword__icontains=query_str)
    return q


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


def run(request):
    return render(request,
                  'automation_test/result/Automation_Test_Report_2017-02-14_115725/Automation_Test_Report_2017-02-14_115725.html')


def test1(request):
    return render(request, 'main/test1.html')


def test2(request):
    return render(request, 'main/test2.html')


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/cases'))
