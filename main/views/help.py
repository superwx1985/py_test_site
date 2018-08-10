import logging
import json
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import Q, CharField
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import SuiteResult, StepResult, CaseResult, Project
from main.forms import OrderByForm, PaginatorForm, SuiteResultForm, StepForm
from utils.other import get_query_condition, change_to_positive_integer, Cookie
from django.template.loader import render_to_string
from main.views import general
from django.template.exceptions import TemplateDoesNotExist

logger = logging.getLogger('django.request')


# 用例列表
@login_required
def list_(request):
    return render(request, 'main/help/list.html', locals())


# 用例详情
@login_required
def detail(request, pk):
    try:
        respond = render(request, 'main/help/detail_{}.html'.format(pk), locals())
    except TemplateDoesNotExist:
        raise Http404
    return respond


@login_required
def delete(request, pk):
    if request.method == 'POST':
        SuiteResult.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


@login_required
def quick_update(request, pk):
    if request.method == 'POST':
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            obj = SuiteResult.objects.get(pk=pk)
            if col_name in ('name', 'keyword'):
                setattr(obj, col_name, new_value)
                obj.clean_fields()
                obj.modifier = request.user
                obj.modified_date = timezone.now()
                obj.save()
            else:
                raise ValueError('非法的字段名称')
        except Exception as e:
            return JsonResponse({'statue': 2, 'message': str(e), 'data': None})
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': new_value})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': None})


@login_required
def step_result_json(_, pk):
    try:
        obj = StepResult.objects.get(pk=pk)
    except StepResult.DoesNotExist:
        raise Http404('StepResult does not exist')
    data_dict = dict()
    data_dict['pk'] = pk
    data_dict['name'] = obj.name
    data_dict['result_message'] = obj.result_message
    data_dict['result_error'] = obj.result_error
    data_dict['step_time'] = render_to_string('main/include/result_time.html', {
        'start_date': obj.start_date, 'end_date': obj.end_date, 'elapsed_time_str': obj.elapsed_time_str})
    data_dict['step_url'] = reverse('step', args=[obj.step.pk])
    data_dict['step_snapshot_url'] = reverse('step_snapshot', args=[pk])
    data_dict['ui_last_url'] = obj.ui_last_url
    data_dict['imgs'] = list()
    if obj.has_sub_case:
        try:
            case_result = CaseResult.objects.get(step_result=pk)
        except CaseResult.DoesNotExist:
            data_dict['sub_case'] = '找不到子用例数据！'
        else:
            data_dict['sub_case'] = render_to_string('main/include/case_result_content.html',
                                                     {'case_result': case_result})
    for img in obj.imgs.all():
        img_dict = dict()
        img_dict['name'] = img.name
        img_dict['url'] = img.img.url
        data_dict['imgs'].append(img_dict)

    return JsonResponse({'statue': 1, 'message': 'OK', 'data': data_dict})


@login_required
def step_result(request, pk):
    try:
        obj = StepResult.objects.get(pk=pk)
    except StepResult.DoesNotExist:
        raise Http404('StepResult does not exist')
    step_url = reverse('step', args=[obj.step.pk])
    step_snapshot_url = reverse('step_snapshot', args=[pk])

    if obj.has_sub_case:
        try:
            case_result = CaseResult.objects.get(step_result=pk)
        except CaseResult.DoesNotExist:
            sub_case = '找不到子用例数据！'

    imgs = list()
    for img in obj.imgs.all():
        img_dict = dict()
        img_dict['name'] = img.name
        img_dict['url'] = img.img.url
        imgs.append(img_dict)

    return render(request, 'main/result/step_result.html', locals())


# 步骤快照
@login_required
def step_snapshot(request, pk):
    action_map_json = general.get_action_map_json()
    try:
        obj = StepResult.objects.get(pk=pk)
    except StepResult.DoesNotExist:
        raise Http404('StepResult does not exist')
    snapshot_obj = json.loads(obj.snapshot)
    form = StepForm(initial=snapshot_obj)
    return render(request, 'main/step/snapshot.html', locals())
