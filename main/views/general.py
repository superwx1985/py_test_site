import logging
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.db import connection
from django.db.models import Q
from django.contrib import auth
from django.contrib.auth.decorators import login_required

logger = logging.getLogger('django.request')


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


# 检查排序条件
def check_order_by(obj, order_by_text):
    try:
        getattr(obj, order_by_text)
    except AttributeError as e:
        logger.warning('排序条件异常', exc_info=True)
        return False
    return True


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


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/cases'))


def debug(request):
    return render(request, 'main/debug.html')


def test1(request):
    return render(request, 'main/test1.html')


def test2(request):
    return render(request, 'main/test2.html')


def debug1(request):
    from py_test.general.execute_step import debug
    result = debug()
    return HttpResponse(result)


def debug2(request):
    return HttpResponse('ok')


