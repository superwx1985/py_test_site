import json
import logging
import copy
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import F, CharField, Value, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import SuiteResult, StepResult, CaseResult, Project
from main.forms import OrderByForm, PaginatorForm, SuiteResultForm
from main.views.general import get_query_condition, change_to_positive_integer
from django.template.loader import render_to_string

logger = logging.getLogger('django.request')


# 用例列表
@login_required
def list_(request):
    if request.method == 'POST':
        page = request.POST.get('page')
        size = request.POST.get('size')
        search_text = request.POST.get('search_text')
        order_by = request.POST.get('order_by')
        order_by_reverse = request.POST.get('order_by_reverse')
        own = request.POST.get('own')
    else:
        page = request.COOKIES.get('page')
        size = request.COOKIES.get('size')
        search_text = request.COOKIES.get('search_text')
        order_by = request.COOKIES.get('order_by')
        order_by_reverse = request.COOKIES.get('order_by_reverse')
        own = request.COOKIES.get('own')

    page = change_to_positive_integer(page)
    size = change_to_positive_integer(size, 10)
    search_text = str(search_text) if search_text else ''
    if order_by is None or order_by == '':
        order_by = 'modified_date'
    if order_by_reverse is None or order_by_reverse == '' or order_by_reverse == 'False':
        order_by_reverse = False
    else:
        order_by_reverse = True
    if own is None or own == '' or own == 'False':
        own = False
    else:
        own = True

    if request.session.get('status', None) == 'success':
        prompt = 'success'
    request.session['status'] = None
    q = get_query_condition(search_text)
    if own:
        objects = SuiteResult.objects.filter(q, is_active=True, creator=request.user).order_by('-start_date').values(
            'pk', 'name', 'keyword', 'project__name', 'start_date', 'result_status', 'creator', 'creator__username',
            'modified_date')
    else:
        objects = SuiteResult.objects.filter(q, is_active=True).order_by('-start_date').values(
            'pk', 'name', 'keyword', 'project__name',  'start_date', 'result_status', 'creator', 'creator__username',
            'modified_date')
    result_status_list = SuiteResult.result_status_list
    d = {l[0]: l[1] for l in result_status_list}
    for o in objects:
        o['result_status_str'] = d.get(o['result_status'], 'N/A')
    # 排序
    if objects:
        if order_by not in objects[0]:
            order_by = 'modified_date'
        if order_by_reverse is True or order_by_reverse == 'True':
            order_by_reverse = True
        else:
            order_by_reverse = False
        objects = sorted(objects, key=lambda x: x[order_by], reverse=order_by_reverse)
    paginator = Paginator(objects, size)
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
        page = 1
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    order_by_form = OrderByForm(initial={'order_by': order_by, 'order_by_reverse': order_by_reverse})
    paginator_form = PaginatorForm(initial={'page': page, 'size': size}, page_max_value=paginator.num_pages)
    return render(request, 'main/result/list.html', locals())


# 用例详情
@login_required
def detail(request, pk):
    try:
        obj = SuiteResult.objects.select_related('creator', 'modifier').get(pk=pk)
    except SuiteResult.DoesNotExist:
        raise Http404('SuiteResult does not exist')
    sub_objects = obj.caseresult_set.filter(step_result=None).order_by('case_order')
    if request.method == 'GET':
        _project = obj.project.pk if obj.project is not None else None
        form = SuiteResultForm(initial={
            'name': obj.name, 'description': obj.description, 'keyword': obj.keyword, 'project': _project})
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/result/detail.html', locals())
    elif request.method == 'POST':
        form = SuiteResultForm(data=request.POST)
        if form.is_valid():
            obj.name = form.data['name']
            obj.description = form.data['description']
            obj.keyword = form.data['keyword']
            project_pk = form.data['project']
            if project_pk.isdigit():
                try:
                    project = Project.objects.get(pk=project_pk)
                    obj.project = project
                except Project.DoesNotExist:
                    logger.warning('ID为[{}]的项目不存在'.format(project_pk))
            else:
                obj.project = None
            obj.modifier = request.user
            obj.clean_fields()
            obj.save()
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('result', args=[pk]) + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/result/detail.html', locals())


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
def step_result_img(request, pk):
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
