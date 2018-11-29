import json
import logging
import copy
import uuid
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import Q, CharField, Value, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import Step
from main.forms import OrderByForm, PaginatorForm, StepForm
from utils.other import get_query_condition, change_to_positive_integer, Cookie, get_project_list, check_admin
from urllib.parse import quote
from main.views import case
from utils import other

logger = logging.getLogger('django.request')


# 步骤列表
@login_required
def list_(request):
    project_list = get_project_list()
    is_admin = check_admin(request.user)

    page = request.GET.get('page')
    size = request.GET.get('size', request.COOKIES.get('size'))
    search_text = request.GET.get('search_text', '')
    order_by = request.GET.get('order_by', 'pk')
    order_by_reverse = request.GET.get('order_by_reverse', 'True')
    all_ = request.GET.get('all_', 'False')
    search_project = request.GET.get('search_project', None)

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

    objects = Step.objects.filter(q).values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
        action=Concat('action__type__name', Value(' - '), 'action__name', output_field=CharField()),
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    # 使用join的方式把多个model结合起来
    # objects = Step.objects.filter(q, is_active=True).order_by('id').select_related('action__type')
    # 分割为多条SQL，然后把结果集用python结合起来
    # objects = Step.objects.filter(q, is_active=True).order_by('id').prefetch_related('action__type')
    # 两者结合使用
    # objects = Step.objects.filter(q, is_active=True).order_by('id').select_related('action').prefetch_related(
    #     'action__type')

    # 获取被调用次数
    reference_objects = Step.objects.filter(is_active=True, case__is_active=True).values('pk').annotate(
        reference_count=Count('*'))
    reference_count = {o['pk']: o['reference_count'] for o in reference_objects}
    for o in objects:
        o['reference_count'] = reference_count.get(o['pk'], 0)

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
    respond = render(request, 'main/step/list.html', locals())
    for cookie in cookies:
        respond.set_cookie(cookie.key, cookie.value, cookie.max_age, cookie.expires, cookie.path)
    return respond


@login_required
def detail(request, pk):
    if request.session.get('status', None) == 'success':
        prompt = 'success'
    request.session['status'] = None

    next_ = request.GET.get('next', '/home/')
    inside = request.GET.get('inside')
    new_pk = request.GET.get('new_pk')
    order = request.GET.get('order')
    reference_url = reverse(reference, args=[pk])  # 被其他对象调用
    action_map_json = other.get_action_map_json()
    is_admin = check_admin(request.user)

    try:
        obj = Step.objects.select_related('creator', 'modifier').get(pk=pk)
    except Step.DoesNotExist:
        raise Http404('Step does not exist')

    if request.method == 'POST' and (is_admin or request.user == obj.creator):
        obj_temp = copy.deepcopy(obj)
        form = StepForm(data=request.POST, instance=obj_temp)
        if form.is_valid():
            obj_temp = form.save(commit=False)
            obj_temp.modifier = request.user
            obj_temp.save()
            form.save_m2m()
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            if redirect:
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect(request.get_full_path())

        return render(request, 'main/step/detail.html', locals())
    else:
        form = StepForm(instance=obj)
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        return render(request, 'main/step/detail.html', locals())


@login_required
def add(request):
    next_ = request.GET.get('next', '/home/')
    inside = request.GET.get('inside')
    action_map_json = other.get_action_map_json()

    parent_project = request.GET.get('parent_project')

    if request.method == 'POST':
        form = StepForm(data=request.POST)
        if form.is_valid():
            obj_temp = form.save(commit=False)
            obj_temp.creator = obj_temp.modifier = request.user
            obj_temp.save()
            form.save_m2m()
            pk = obj_temp.id
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            if redirect == 'add_another':
                return HttpResponseRedirect(request.get_full_path())
            elif redirect:
                return HttpResponseRedirect(next_)
            else:
                # 如果是内嵌网页，则加上内嵌标志后再跳转
                para = ''
                if inside:
                    para = '&inside=1&new_pk={}'.format(pk)
                return HttpResponseRedirect('{}?next={}{}'.format(reverse(detail, args=[pk]), quote(next_), para))

        return render(request, 'main/step/detail.html', locals())
    else:
        if parent_project:
            form = StepForm(initial={'project': parent_project})
        else:
            form = StepForm()
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        return render(request, 'main/step/detail.html', locals())


@login_required
def delete(request, pk):
    err = None
    if request.method == 'POST':
        try:
            obj = Step.objects.select_related('creator', 'modifier').get(pk=pk)
        except Step.DoesNotExist:
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
        return JsonResponse({'status': 2, 'message': err, 'data': pk})
    else:
        return JsonResponse({'status': 1, 'message': 'OK', 'data': pk})


@login_required
def multiple_delete(request):
    if request.method == 'POST':
        try:
            pk_list = json.loads(request.POST['pk_list'])
            is_admin = check_admin(request.user)
            if is_admin:
                Step.objects.filter(pk__in=pk_list).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
            else:
                Step.objects.filter(pk__in=pk_list, creator=request.user).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
        except Exception as e:
            return JsonResponse({'status': 2, 'message': str(e), 'data': None})
        return JsonResponse({'status': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'status': 2, 'message': 'Only accept "POST" method', 'data': []})


@login_required
def quick_update(request, pk):
    if request.method == 'POST':
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            obj = Step.objects.get(pk=pk)
            if col_name in ('name', 'keyword'):
                setattr(obj, col_name, new_value)
                obj.clean_fields()
                obj.modifier = request.user
                obj.modified_date = timezone.now()
                obj.save()
            else:
                raise ValueError('非法的字段名称')
        except Exception as e:
            return JsonResponse({'status': 2, 'message': str(e), 'data': None})
        return JsonResponse({'status': 1, 'message': 'OK', 'data': new_value})
    else:
        return JsonResponse({'status': 2, 'message': 'Only accept "POST" method', 'data': None})


# 获取全部step，使用用序列化的方法
# @login_required
# def step_list_all_old(request):
#     objects = Step.objects.filter(is_active=True).order_by('id').select_related(
#         'action', 'creator', 'modifier', 'action__type')
#     json_ = serializers.serialize('json', objects, use_natural_foreign_keys=True)
#     data_dict = dict()
#     data_dict['data'] = json_
#     return JsonResponse({'status': 1, 'message': 'OK', 'data': json_})


# 获取m2m json
@login_required
def list_json(request):
    condition = request.POST.get('condition', '{}')
    try:
        condition = json.loads(condition)
    except json.decoder.JSONDecodeError:
        condition = dict()

    page = condition.get('page')
    size = 10
    search_text = condition.get('search_text', '')
    order_by = condition.get('order_by', 'pk')
    order_by_reverse = condition.get('order_by_reverse', 'True')
    all_ = condition.get('all_', 'False')
    search_project = condition.get('search_project', None)

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

    objects = Step.objects.filter(q).values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
        action=Concat('action__type__name', Value(' - '), 'action__name', output_field=CharField()),
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
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

    for obj in objects:
        obj['url'] = reverse(detail, args=[obj['pk']])
        obj['modified_date_sort'] = obj['modified_date'].strftime('%Y-%m-%d')
        obj['modified_date'] = obj['modified_date'].strftime('%Y-%m-%d %H:%M:%S')

    return JsonResponse({'status': 1, 'message': 'OK', 'data': {
        'objects': list(objects), 'page': page, 'max_page': paginator.num_pages, 'size': size}})


# 获取临时m2m
@login_required
def list_temp(request):
    pk_list = json.loads(request.POST.get('condition', ''))
    order = 0
    data_list = list()
    for pk in pk_list:
        if pk.strip() == '':
            continue
        objects = Step.objects.filter(pk=pk).values(
            'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
            action=Concat('action__type__name', Value(' - '), 'action__name', output_field=CharField()),
            real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
        if not objects:
            continue
        objects = list(objects)
        order += 1
        obj = objects[0]
        obj['order'] = order
        obj['url'] = reverse(detail, args=[pk])
        obj['modified_date_sort'] = obj['modified_date'].strftime('%Y-%m-%d')
        obj['modified_date'] = obj['modified_date'].strftime('%Y-%m-%d %H:%M:%S')
        data_list.append(obj)
    return JsonResponse({'status': 1, 'message': 'OK', 'data': data_list})


# 复制操作
def copy_action(pk, user, name_prefix=None, copy_sub_item=None, copied_items=None, call_items=None):
    obj = Step.objects.select_related('action').get(pk=pk)
    obj.pk = None
    if name_prefix:
        obj.name = name_prefix + obj.name
        if len(obj.name) > 100:
            obj.name = obj.name[0:97] + '...'

    if not copied_items:
        copied_items = [dict()]
    if not call_items:
        call_items = [list()]
    call_items[0].append(obj)
    if copy_sub_item and obj.action.code == 'OTHER_CALL_SUB_CASE' and obj.other_sub_case:
        # 判断是否已被复制
        if copied_items[0] and obj.other_sub_case in copied_items[0]:
            obj.other_sub_case = copied_items[0][obj.other_sub_case]
        else:
            new_sub_obj = case.copy_action(
                obj.other_sub_case.pk, user, name_prefix, copy_sub_item, copied_items, call_items)
            copied_items[0][obj.other_sub_case] = new_sub_obj
            obj.other_sub_case = new_sub_obj
    obj.creator = obj.modifier = user
    obj.uuid = uuid.uuid1()
    obj.clean_fields()
    obj.save()
    return obj


# 复制
@login_required
def copy_(request, pk):
    name_prefix = request.POST.get('name_prefix', '')
    order = request.POST.get('order')
    order = change_to_positive_integer(order, 0)
    try:
        obj = copy_action(pk, request.user, name_prefix)
        return JsonResponse({
            'status': 1, 'message': 'OK', 'data': {
                'new_pk': obj.pk, 'new_url': reverse(detail, args=[obj.pk]), 'order': order}
        })
    except Exception as e:
        return JsonResponse({'status': 2, 'message': str(e), 'data': None})


# 批量复制
@login_required
def multiple_copy(request):
    if request.method == 'POST':
        try:
            pk_list = json.loads(request.POST['pk_list'])
            name_prefix = request.POST.get('name_prefix', '')
            for pk in pk_list:
                _ = copy_action(pk, request.user, name_prefix)
        except Exception as e:
            return JsonResponse({'status': 2, 'message': str(e), 'data': None})
        return JsonResponse({'status': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'status': 2, 'message': 'Only accept "POST" method', 'data': []})


# 获取调用列表
def reference(request, pk):
    try:
        obj = Step.objects.get(pk=pk)
    except Step.DoesNotExist:
        raise Http404('Step does not exist')
    objects = obj.case_set.filter(is_active=True).order_by('-modified_date').values(
        'pk', 'uuid', 'name', 'keyword', 'creator', 'creator__username', 'modified_date', 'casevsstep__order').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj_ in objects:
        obj_['url'] = '{}?next={}'.format(reverse(case.detail, args=[obj_['pk']]), reverse(case.list_))
        obj_['type'] = '用例'
        obj_['order'] = obj_['casevsstep__order']
    return render(request, 'main/include/detail_reference.html', locals())

