import logging
import json
from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from main.forms import *

logger = logging.getLogger('django.request')


# 变量组快照
@login_required
def variable_group_snapshot(request, pk):
    try:
        obj = CaseResult.objects.get(pk=pk)
    except CaseResult.DoesNotExist:
        raise Http404('Case Result does not exist')
    else:
        _ = obj.snapshot["variable_group"]
        variables_json = json.dumps({'data': _['variables']})
        form = VariableGroupForm(initial=_)
        return render(request, 'main/variable_group/snapshot.html', locals())


# 数据组快照
@login_required
def data_set_snapshot(request, pk):
    try:
        obj = CaseResult.objects.get(pk=pk)
    except CaseResult.DoesNotExist:
        raise Http404('Case Result does not exist')
    else:
        form = DataSetForm(initial=obj.snapshot["data_set"])
        return render(request, 'main/data_set/snapshot.html', locals())


@login_required
def config_snapshot(request, pk):
    try:
        obj = CaseResult.objects.get(pk=pk)
    except CaseResult.DoesNotExist:
        raise Http404('Suite Result does not exist')
    else:
        form = ConfigForm(initial=obj.snapshot["config"])
        return render(request, 'main/config/snapshot.html', locals())