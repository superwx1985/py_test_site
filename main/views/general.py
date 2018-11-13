import logging
import json
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.contrib.auth.models import Group


logger = logging.getLogger('django.request')


# 跳转
def redirect(request):
    next_ = request.GET.get('next', '/home/')
    return HttpResponseRedirect(next_)


def version(request):
    return render(request, 'main/other/version.html')


# 验证是否管理员
def is_admin(user):
    try:
        admin_group = Group.objects.get(name='QA_leader')
    except Group.DoesNotExist:
        admin_group = None
    if admin_group in user.groups.all():
        return True
    else:
        return False


def debug(request):
    return render(request, 'main/debug.html')


def test1(request):
    return render(request, 'main/test1.html')


def test2(request):
    return render(request, 'main/test2.html')


def debug1(_):
    return HttpResponse('debug1')


def debug2(_):
    return HttpResponse('ok')


def debug3(_):
    data_dict = {'a': 'av', 'b': u'bv', u'c': u'cv', '一': '一VVV', '二': u'二VVV', u'三': u'三'}

    return HttpResponse(json.dumps({'status': 1, 'message': 'OK', 'data': data_dict, '测试': '测试VVV'}))



