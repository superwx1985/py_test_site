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



