import logging
import json
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render


logger = logging.getLogger('django.request')


# 跳转
def redirect(request):
    next_ = request.GET.get('next', '/home/')
    return HttpResponseRedirect(next_)


def version(request):
    return render(request, 'main/other/version.html')


def debug(request):
    return render(request, 'main/debug.html')


def test1(request):
    return render(request, 'main/test1.html')


def test2(request):
    return render(request, 'main/test2.html')


def debug1(request):
    from py_test.general.vic_step import debug
    result = debug()
    return HttpResponse(result)


def debug2(request):
    return HttpResponse('ok')


def debug3(request):
    data_dict = {'a': 'av', 'b': u'bv', u'c': u'cv', '一': '一VVV', '二': u'二VVV', u'三': u'三'}

    return HttpResponse(json.dumps({'statue': 1, 'message': 'OK', 'data': data_dict, '测试': '测试VVV'}))
