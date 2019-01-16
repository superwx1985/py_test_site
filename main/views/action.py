import json
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from main.models import Action

logger = logging.getLogger('django.request')


# 获取带搜索信息的下拉列表数据
@login_required
def select_json(request):
    condition = request.POST.get('condition', '{}')
    try:
        condition = json.loads(condition)
    except json.decoder.JSONDecodeError:
        condition = dict()
    selected_pk = condition.get('selected_pk')
    objects = Action.objects.filter(is_active=True).values('pk', 'name', 'type__name')

    data = list()
    for obj in objects:
        d = dict()
        d['id'] = str(obj['pk'])
        d['name'] = '{} - {}'.format(obj['type__name'], obj['name'])
        d['search_info'] = '{} {}'.format(obj['name'], obj['type__name'])
        if str(obj['pk']) == selected_pk:
            d['selected'] = True
        else:
            d['selected'] = False
        data.append(d)

    return JsonResponse({'state': 1, 'message': 'OK', 'data': data})

