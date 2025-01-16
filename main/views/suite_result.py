import logging
import json
import datetime
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import Q, CharField, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import SuiteResult, Step, Suite, result_state_list
from main.forms import OrderByForm, PaginatorForm, SuiteResultForm, ConfigForm, VariableGroupForm, ElementGroupForm
from utils.other import get_query_condition, change_to_positive_integer, Cookie, get_project_list, check_admin
from py_test.vic_tools.vic_date_handle import get_timedelta_str

logger = logging.getLogger('django.request')


# 列表
@login_required
def list_(request):
    if request.session.get('state', None) == 'success':
        prompt = 'success'
    request.session['state'] = None

    project_list = get_project_list()
    is_admin = check_admin(request.user)

    page = request.GET.get('page')
    size = request.GET.get('size', request.COOKIES.get('size'))
    search_text = request.GET.get('search_text', '')
    order_by = request.GET.get('order_by', 'pk')
    order_by_reverse = request.GET.get('order_by_reverse', 'True')
    all_ = request.GET.get('all_', 'False')
    search_project = request.GET.get('search_project', None)
    suite_id = request.GET.get('suite_id', None)

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
    if search_project in ('', 'None'):
        search_project = None

    q = get_query_condition(search_text)
    q &= Q(is_active=True)
    if not all_:
        q &= Q(creator=request.user)
    if search_project:
        q &= Q(project=search_project)
    if suite_id:
        try:
            obj = Suite.objects.get(pk=suite_id)
        except Suite.DoesNotExist:
            raise Http404('Suite does not exist')
        q &= Q(suite=obj)

    objects = SuiteResult.objects.filter(q).values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date', 'suite__pk',
        'start_date', 'end_date', 'result_state').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))

    d = {l[0]: l[1] for l in result_state_list}
    m2m_objects = SuiteResult.objects.filter(
        # is_active=True, caseresult__case_order__isnull=False).values('pk').annotate(
        is_active=True, caseresult__step_result__isnull=True).values('pk').annotate(
        m2m_count=Count('caseresult'))
    m2m_count = {o['pk']: o['m2m_count'] for o in m2m_objects}
    for o in objects:
        # 获取状态文字
        o['result_state_str'] = d.get(o['result_state'], 'N/A')
        # 获取耗时
        # 为了减少查询数据库，没有使用models里的方法
        if o['end_date'] is None or o['start_date'] is None:
            o['elapsed_time'] = datetime.timedelta(days=9999)
        else:
            o['elapsed_time'] = o['end_date'] - o['start_date']
        if o['elapsed_time'] >= datetime.timedelta(days=9999):
            o['elapsed_time_str'] = 'N/A'
        else:
            o['elapsed_time_str'] = get_timedelta_str(o['elapsed_time'], 1)
        # 获取子对象数量
        o['m2m_count'] = m2m_count.get(o['pk'], 0)
    # 排序
    if objects:
        if order_by not in objects[0]:
            order_by = 'pk'
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


@login_required
def detail(request, pk):
    next_ = request.GET.get('next', '')
    inside = request.GET.get('inside')
    is_admin = check_admin(request.user)

    try:
        obj = SuiteResult.objects.select_related('creator', 'modifier').get(pk=pk)
    except SuiteResult.DoesNotExist:
        raise Http404('Suite Result does not exist')
    sub_objects = obj.caseresult_set.filter(step_result=None)

    if request.method == 'POST' and (is_admin or request.user == obj.creator):
        import copy
        obj_temp = copy.deepcopy(obj)
        form = SuiteResultForm(data=request.POST, instance=obj_temp)
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.modifier = request.user
            form_.save()
            form.save_m2m()
            request.session['state'] = 'success'
            redirect = request.POST.get('redirect')
            if redirect:
                if not next_:
                    next_ = reverse(list_)
                    request.session['state'] = None
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect(request.get_full_path())

        return render(request, 'main/result/detail.html', locals())
    else:
        _project = obj.project.pk if obj.project is not None else None
        form = SuiteResultForm(instance=obj)
        if request.session.get('state', None) == 'success':
            prompt = 'success'
        request.session['state'] = None
        return render(request, 'main/result/detail.html', locals())


@login_required
def delete(request, pk):
    err = None
    if request.method == 'POST':
        try:
            obj = SuiteResult.objects.select_related('creator', 'modifier').get(pk=pk)
        except SuiteResult.DoesNotExist:
            err = '对象不存在'
        else:
            is_admin = check_admin(request.user)
            if is_admin or obj.creator == request.user:
                obj.is_active = False
                obj.modifier = request.user
                obj.save()
            else:
                err = '无权限'
    else:
        err = '无效请求'

    if err:
        return JsonResponse({'state': 2, 'message': err, 'data': pk})
    else:
        return JsonResponse({'state': 1, 'message': 'OK', 'data': pk})


@login_required
def multiple_delete(request):
    if request.method == 'POST':
        try:
            pk_list = json.loads(request.POST['pk_list'])
            is_admin = check_admin(request.user)
            if is_admin:
                SuiteResult.objects.filter(pk__in=pk_list).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
            else:
                SuiteResult.objects.filter(pk__in=pk_list, creator=request.user).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
        except Exception as e:
            return JsonResponse({'state': 2, 'message': str(e), 'data': None})
        return JsonResponse({'state': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'state': 2, 'message': 'Only accept "POST" method', 'data': []})


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
            return JsonResponse({'state': 2, 'message': str(e), 'data': None})
        return JsonResponse({'state': 1, 'message': 'OK', 'data': new_value})
    else:
        return JsonResponse({'state': 2, 'message': 'Only accept "POST" method', 'data': None})


# 配置快照
@login_required
def config_snapshot(request, pk):
    try:
        obj = SuiteResult.objects.get(pk=pk)
    except SuiteResult.DoesNotExist:
        raise Http404('Suite Result does not exist')
    else:
        form = ConfigForm(initial=obj.config)
        return render(request, 'main/config/snapshot.html', locals())


# 变量组快照
@login_required
def variable_group_snapshot(request, pk):
    try:
        obj = SuiteResult.objects.get(pk=pk)
    except SuiteResult.DoesNotExist:
        raise Http404('Suite Result does not exist')
    else:
        variables_json = json.dumps({'data': obj.variable_group['variables']})
        form = VariableGroupForm(initial=obj.variable_group)
        return render(request, 'main/variable_group/snapshot.html', locals())


# 元素组快照
@login_required
def element_group_snapshot(request, pk):
    try:
        obj = SuiteResult.objects.get(pk=pk)
    except SuiteResult.DoesNotExist:
        raise Http404('Suite Result does not exist')
    else:
        elements_json = json.dumps({'data': obj.element_group['elements']})
        by_list_json = json.dumps(Step.ui_by_list)
        form = ElementGroupForm(initial=obj.element_group)
        return render(request, 'main/element_group/snapshot.html', locals())
