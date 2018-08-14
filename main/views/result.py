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
from utils import other

logger = logging.getLogger('django.request')


# 用例列表
@login_required
def list_(request):
    page = request.GET.get('page')
    size = request.GET.get('size', request.COOKIES.get('size'))
    search_text = str(request.GET.get('search_text', ''))
    order_by = request.GET.get('order_by', 'modified_date')
    order_by_reverse = request.GET.get('order_by_reverse', 'True')
    all_ = request.GET.get('all_', 'False')

    page = change_to_positive_integer(page, 1)
    size = change_to_positive_integer(size, 10)
    if order_by_reverse == 'True':
        order_by_reverse = True
    else:
        order_by_reverse = False
    if all_ == 'False':
        all_ = False
    else:
        all_ = True

    if request.session.get('status', None) == 'success':
        prompt = 'success'
    request.session['status'] = None
    q = get_query_condition(search_text)
    if all_:
        q &= Q(is_active=True)
    else:
        q &= Q(is_active=True) & Q(creator=request.user)
    objects = SuiteResult.objects.filter(q).values(
        'pk', 'uuid', 'name', 'keyword', 'project__name',  'start_date', 'result_status', 'creator', 'creator__username',
        'modified_date').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    result_status_list = SuiteResult.result_status_list
    d = {l[0]: l[1] for l in result_status_list}
    for o in objects:
        o['result_status_str'] = d.get(o['result_status'], 'N/A')
    # 排序
    if objects:
        if order_by not in objects[0]:
            order_by = 'modified_date'
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
    # 设置cookie
    cookies = [Cookie('size', size, path=request.path)]
    respond = render(request, 'main/result/list.html', locals())
    for cookie in cookies:
        respond.set_cookie(cookie.key, cookie.value, cookie.max_age, cookie.expires, cookie.path)
    return respond


# 用例详情
@login_required
def detail(request, pk):
    next_ = request.GET.get('next', '/home/')
    inside = request.GET.get('inside')
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
            obj.name = form.cleaned_data['name']
            obj.description = form.cleaned_data['description']
            obj.keyword = form.cleaned_data['keyword']
            project_pk = form.cleaned_data['project']
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
            if redirect:
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect(request.get_full_path())

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
    action_map_json = other.get_action_map_json()
    try:
        obj = StepResult.objects.get(pk=pk)
    except StepResult.DoesNotExist:
        raise Http404('StepResult does not exist')
    snapshot_obj = json.loads(obj.snapshot)
    form = StepForm(initial=snapshot_obj)
    return render(request, 'main/step/snapshot.html', locals())
