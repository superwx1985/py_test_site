import logging
from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.exceptions import TemplateDoesNotExist

logger = logging.getLogger('django.request')


@login_required
def detail(request):
    try:
        respond = render(request, 'main/maintenance/detail.html', locals())
    except TemplateDoesNotExist:
        raise Http404
    return respond
