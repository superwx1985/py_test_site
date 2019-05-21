import logging
import json
import traceback
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.exceptions import TemplateDoesNotExist
from py_test.general import vic_method, vic_variables
from main.models import VariableGroup

logger = logging.getLogger('django.request')


# 帮助列表
@login_required
def list_(request):
    return render(request, 'main/help/list.html', locals())


# 帮助详情
@login_required
def detail(request, pk):
    try:
        respond = render(request, 'main/help/detail_{}.html'.format(pk), locals())
    except TemplateDoesNotExist:
        raise Http404
    return respond


# 变量测试
def variable_test(request):
    condition = json.loads(request.POST.get('condition'))
    variable_str = condition.get('variable_str')
    variable_group_pk = condition.get('variable_group_pk')

    success = False
    data = dict()
    if condition.get:
        try:
            global_variables = vic_variables.Variables()
            if variable_group_pk and variable_group_pk != 'null':
                variable_group = VariableGroup.objects.get(pk=variable_group_pk)
                variable_objects = variable_group.variable_set.all()
                for obj in variable_objects:
                    value = vic_method.replace_special_value(obj.value, global_variables)
                    global_variables.set_variable(obj.name, value)
            value = vic_method.replace_special_value(variable_str, global_variables)
            data['value'] = value
            data['value_type'] = str(type(value))
            msg = '测试成功'
            success = True
        except Exception as e:
            msg = '{}\n{}'.format(getattr(e, 'msg', str(e)), traceback.format_exc())
            traceback.format_exc()
    else:
        msg = '无测试数据'

    if success:
        return JsonResponse({'state': 1, 'message': msg, 'data': data})
    else:
        return JsonResponse({'state': 2, 'message': msg, 'data': data})
