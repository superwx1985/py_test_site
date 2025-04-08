import logging
import json
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


logger = logging.getLogger('django.request')


# 跳转
def redirect(request):
    next_ = request.GET.get('next', '/home/')
    return HttpResponseRedirect(next_)


def version(request):
    return render(request, 'main/other/version.html')


@login_required
def delete_unused(_):
    pass


@login_required
def clear_db(_):
    pass


def debug(request):
    return render(request, 'main/other/debug.html', locals())


def test1(request):
    return render(request, 'main/other/test1.html')


def test2(request):
    return render(request, 'main/other/test2.html')


def test3(request):
    return render(request, 'main/other/test3.html')


def debug1(_):
    return HttpResponse('debug1')


def debug2(_):
    return HttpResponse('ok')


def debug3(_):
    data_dict = {'a': 'av', 'b': u'bv', u'c': u'cv', '一': '一VVV', '二': u'二VVV', u'三': u'三'}

    return HttpResponse(json.dumps({'state': 1, 'message': 'OK', 'data': data_dict, '测试': '测试VVV'}))


# 列表元素排序
def sort_list(objects, order_by, order_by_reverse):
    if order_by not in objects[0]:
        order_by = 'pk'
    # 处理 None 值，确保安全排序
    return sorted(
        objects,
        key=lambda x: (x[order_by] is not None, x[order_by]),  # None 作为最小值
        reverse=order_by_reverse
    )


def generate_new_name(name, new_name, name_prefix):
    if new_name:
        name = new_name
    elif name_prefix:
        name = name_prefix + name
    if len(name) > 100:
        name = name[0:97] + '...'
    return name
