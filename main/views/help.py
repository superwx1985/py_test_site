import logging
import json
import traceback
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.exceptions import TemplateDoesNotExist
from py_test.general import vic_method, vic_variables
from main.models import VariableGroup
from py_test.vic_tools import vic_find_object, vic_eval

logger = logging.getLogger('django.request')


# 帮助列表
@login_required
def list_(request):
    return render(request, 'main/help/list.html', locals())


# 帮助详情
@login_required
def detail(request, pk):
    inside = request.GET.get('inside')
    try:
        respond = render(request, 'main/help/detail_{}.html'.format(pk), locals())
    except TemplateDoesNotExist:
        raise Http404
    return respond


def get_variables(variable_group_pk):
    variables = vic_variables.Variables()
    if variable_group_pk and variable_group_pk != 'null':
        variable_group = VariableGroup.objects.get(pk=variable_group_pk)
        variable_objects = variable_group.variable_set.all()
        for obj in variable_objects:
            value = vic_method.replace_special_value(obj.value, variables, logger=logger)
            variables.set_variable(obj.name, value)
    return variables


# 变量表达式测试
def variable_test(request):
    condition = json.loads(request.POST.get('condition'))
    test_input = condition.get('test_input')
    variable_group_pk = condition.get('variable_group_pk')

    msg = '错误'
    state = 2
    data = dict()
    if test_input:
        process = f"{test_input}\n替换${{}}$标识的变量 =====>"
        try:
            variables = get_variables(variable_group_pk)
            value = vic_method.replace_special_value(test_input, variables, logger=logger)
            process = f"{process}\n{value}\n替换$[]$标识的变量 =====>"

            variable_dict = vic_variables.get_variable_dict(variables)
            eo = vic_eval.EvalObject(value, variable_dict, logger)
            eval_success, eval_result, final_expression = eo.get_eval_result()
            process = f"{process}\n{final_expression}\n计算表达式 =====>\n{eval_result}"
            detail_msg = ""
            if eval_success:
                msg = '成功'
                state = 1
            else:
                detail_msg = f"不合法的表达式【{final_expression}】\n错误信息：{eval_result}\n注意：字符串应该用英文引号括起来，检查引入的变量是否未定义"

            data['value'] = str(eval_result)
            data['value_type'] = type(eval_result).__name__
            data['detail_msg'] = detail_msg
            data['process'] = process
        except Exception as e:
            data['value'] = f"{getattr(e, 'msg', str(e))}"
            data['value_type'] = type(e).__name__
            data['detail_msg'] = f'{traceback.format_exc()}'
            data['process'] = process
    else:
        msg = '无测试数据'

    return JsonResponse({'state': state, 'message': msg, 'data': data})


# 文本验证操作符测试
def text_verification_test(request):
    condition = json.loads(request.POST.get('condition'))
    test_input = condition.get('test_input')
    text_expression = condition.get('text_expression')
    variable_group_pk = condition.get('variable_group_pk')

    success = False
    data = dict()
    if condition.get('test_input'):
        try:
            variables = get_variables(variable_group_pk)
            value = vic_method.replace_special_value(test_input, variables, logger=logger)
            expression = vic_method.replace_special_value(text_expression, variables, logger=logger)
            find_result = vic_find_object.find_with_condition(expression, value, logger=logger)
            data['value'] = value
            data['find_result'] = str(find_result)
            data['re_result'] = find_result.re_result[0] if find_result.re_result else None
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
