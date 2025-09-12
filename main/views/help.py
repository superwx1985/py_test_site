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
            passed, pass_group, fail_group, condition_count, data_object = vic_find_object.find_with_multiple_condition(expression, value, logger=logger)
            data['value'] = value
            data['passed'] = passed

            data['re_result'] = None
            if passed and len(pass_group) == 1:
                try:  # 先判断存在，再使用
                    if len(pass_group[0][1]) == 1:
                        data['re_result'] = pass_group[0][1][0][2].re_result[0]
                except (IndexError, TypeError):
                    # 路径不存在时的处理
                    pass

            pass_group_str = ""
            fail_group_str = ""

            def generate_keyword_str(result):
                param = ""
                expect_count = "n"
                if result.operator_list:
                    param = str(result.operator_list)
                    if "count" in result.operator_list:
                        expect_count = result.operator_list[1]
                str_ = f"{result.condition_value}\nCount \t[{result.match_count}]\nExpect\t[{expect_count}]\nParam\t{param}\n"
                return str_

            if 0 < len(pass_group):
                pass_group_str += f"\n===== Pass Group [{len(pass_group)}/{condition_count}] =====\n"
                for group_i in pass_group:
                    pass_group_str += f"----- Group {group_i[0]} -----\n"
                    str_p = ""
                    str_f = ""
                    if 0 < len(group_i[1]):
                        str_p = f"Pass keyword: [{len(group_i[1])}/{len(group_i[1])+len(group_i[2])}]"
                        j = 0
                        for v in group_i[1]:
                            j += 1
                            str_p += f"\n*** Keyword {str(j)} ***\n{generate_keyword_str(v[2])}"
                    if 0 < len(group_i[2]):
                        str_f = f"Fail keyword: [{len(group_i[2])}/{len(group_i[1])+len(group_i[2])}]"
                        j = 0
                        for v in group_i[2]:
                            j += 1
                            str_f += f"\n*** Keyword {str(j)} ***\n{generate_keyword_str(v[2])}"
                    pass_group_str = pass_group_str + str_p + str_f

            if 0 < len(fail_group):
                fail_group_str += f"\n===== Fail Group [{len(fail_group)}/{condition_count}] =====\n"
                for group_i in fail_group:
                    fail_group_str += f"----- Group {group_i[0]} -----\n"
                    str_p = ""
                    str_f = ""
                    if 0 < len(group_i[1]):
                        str_p = f"Pass keyword: [{len(group_i[1])}/{len(group_i[1])+len(group_i[2])}]"
                        j = 0
                        for v in group_i[1]:
                            j += 1
                            str_p += f"\n*** Keyword {str(j)} ***\n{generate_keyword_str(v[2])}"
                    if 0 < len(group_i[2]):
                        str_f = f"Fail keyword: [{len(group_i[2])}/{len(group_i[1])+len(group_i[2])}]"
                        j = 0
                        for v in group_i[2]:
                            j += 1
                            str_f += f"\n*** Keyword {str(j)} ***\n{generate_keyword_str(v[2])}"
                    fail_group_str = fail_group_str + str_p + str_f

            data['find_result'] = pass_group_str + fail_group_str

            msg = "测试成功"
            success = True
        except Exception as e:
            msg = '{}\n{}'.format(getattr(e, 'msg', str(e)), traceback.format_exc())
            traceback.format_exc()
    else:
        msg = "无测试数据"

    if success:
        return JsonResponse({'state': 1, 'message': msg, 'data': data})
    else:
        return JsonResponse({'state': 2, 'message': msg, 'data': data})
