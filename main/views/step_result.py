import logging
import json
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from main.models import StepResult, CaseResult
from main.forms import StepForm
from django.template.loader import render_to_string
from utils import other

logger = logging.getLogger('django.request')


@login_required
def detail(request, pk):
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


@login_required
def detail_json(_, pk):
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


# 步骤快照
@login_required
def snapshot(request, pk):
    # 获取action映射json
    action_map_json = other.get_action_map_json()
    try:
        obj = StepResult.objects.get(pk=pk)
    except StepResult.DoesNotExist:
        raise Http404('StepResult does not exist')
    try:
        snapshot_obj = json.loads(obj.snapshot)
    except:
        logger.warning('快照数据损坏，无法展示。', exc_info=True)
        return HttpResponse('<div style="color: red;">快照数据损坏，无法展示。</div>')
    else:
        form = StepForm(initial=snapshot_obj)
        return render(request, 'main/step/snapshot.html', locals())
