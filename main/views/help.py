import logging
from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.exceptions import TemplateDoesNotExist

logger = logging.getLogger('django.request')


# 帮助列表
@login_required
def list_(request):
    return render(request, 'main/help/list.html', locals())


# 帮组详情
@login_required
def detail(request, pk):
    try:
        respond = render(request, 'main/help/detail_{}.html'.format(pk), locals())
    except TemplateDoesNotExist:
        raise Http404
    return respond
