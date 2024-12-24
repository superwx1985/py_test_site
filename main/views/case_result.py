import logging
import json
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from main.models import CaseResult
from main.forms import VariableGroupForm

logger = logging.getLogger('django.request')


# 变量组快照
@login_required
def variable_group_snapshot(request, pk):
    try:
        obj = CaseResult.objects.get(pk=pk)
    except CaseResult.DoesNotExist:
        raise Http404('Case Result does not exist')
    try:
        snapshot_obj = json.loads(obj.variable_group)
        variables_json = json.dumps({'data': snapshot_obj['variables']})
    except:
        logger.warning('快照数据损坏，无法展示。', exc_info=True)
        return HttpResponse('<div style="color: red;">快照数据损坏，无法展示。</div>')
    else:
        form = VariableGroupForm(initial=snapshot_obj)
        return render(request, 'main/variable_group/snapshot.html', locals())
