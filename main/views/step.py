import json
import logging
import copy
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render, get_object_or_404
from django.core.serializers import serialize
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db import connection
from django.db.models import Q, F, CharField, Value, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core import serializers
# from django.views.decorators.csrf import csrf_exempt
from main.models import Step, Action
from main.forms import OrderByForm, PaginatorForm, StepForm
from main.views.general import get_query_condition

logger = logging.getLogger('django.request')


# 步骤列表
@login_required
def list_(request):
    if request.method == 'POST':
        page = int(request.POST.get('page', 1)) if request.POST.get('page') != '' else 1
        if page <= 0:
            page = 1
        size = int(request.POST.get('size', 5)) if request.POST.get('size') != '' else 10
        search_text = str(request.POST.get('search_text', ''))
        order_by = request.POST.get('order_by', 'modified_date')
        order_by_reverse = request.POST.get('order_by_reverse', False)
        own = request.POST.get('own_checkbox')
    else:
        page = int(request.COOKIES.get('page', 1))
        size = int(request.COOKIES.get('size', 10))
        search_text = ''
        order_by = 'modified_date'
        order_by_reverse = True  # 是否倒序
        own = True
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
    q = get_query_condition(search_text)
    if own:
        objects = Step.objects.filter(q, is_active=True, creator=request.user).values(
            'pk', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
            action=Concat('action__type__name', Value(' - '), 'action__name', output_field=CharField()))
    else:
        objects = Step.objects.filter(q, is_active=True).values(
            'pk', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
            action=Concat('action__type__name', Value(' - '), 'action__name', output_field=CharField()))
    # 使用join的方式把多个model结合起来
    # objects = Step.objects.filter(q, is_active=True).order_by('id').select_related('action__type')
    # 分割为多条SQL，然后把结果集用python结合起来
    # objects = Step.objects.filter(q, is_active=True).order_by('id').prefetch_related('action__type')
    # 两者结合使用
    # objects = Step.objects.filter(q, is_active=True).order_by('id').select_related('action').prefetch_related(
    #     'action__type')
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
    return render(request, 'main/step/list.html', locals())


@login_required
def detail(request, pk):
    try:
        obj = Step.objects.select_related('creator', 'modifier').get(pk=pk)
    except Step.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        related_objects = obj.case_set.filter(is_active=True)
        form = StepForm(instance=obj)
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/step/detail.html', locals())
    elif request.method == 'POST':
        obj_temp = copy.deepcopy(obj)
        form = StepForm(data=request.POST, instance=obj_temp)
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = obj.creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            form.save_m2m()
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('step', args=[pk]) + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/step/detail.html', locals())


@login_required
def add(request):
    if request.method == 'GET':
        form = StepForm()
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/step/detail.html', locals())
    elif request.method == 'POST':
        form = StepForm(data=request.POST)
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = request.user
            form_.modifier = request.user
            form_.is_active = True
            form_.save()
            form.save_m2m()
            pk = form_.id
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('step', args=[pk]) + '?redirect_url=' + redirect_url)
            elif redirect == 'add_another':
                return HttpResponseRedirect(reverse('step_add') + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/step/detail.html', locals())


@login_required
def delete(request, pk):
    if request.method == 'POST':
        Step.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


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
            return JsonResponse({'statue': 2, 'message': str(e), 'data': None})
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': new_value})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': None})


# 获取全部step，使用用序列化的方法
# @login_required
# def step_list_all_old(request):
#     objects = Step.objects.filter(is_active=True).order_by('id').select_related(
#         'action', 'creator', 'modifier', 'action__type')
#     json_ = serializers.serialize('json', objects, use_natural_foreign_keys=True)
#     data_dict = dict()
#     data_dict['data'] = json_
#     return JsonResponse({'statue': 1, 'message': 'OK', 'data': json_})


# 获取step list json
@login_required
def list_json(request):
    condition = request.POST.get('condition', '{}')
    try:
        condition = json.loads(condition)
    except json.decoder.JSONDecodeError:
        condition = dict()

    page = int(condition.get('page', 1)) if condition.get('page') != '' else 1
    if page <= 0:
        page = 1
    size = 10
    search_text = condition.get('search_text', '')
    order_by = condition.get('order_by', 'create_date')
    order_by_reverse = condition.get('order_by_reverse', False)
    own = condition.get('own_checkbox')
    q = get_query_condition(search_text)
    if own:
        objects = Step.objects.filter(q, is_active=True, creator=request.user).values(
            'pk', 'name', 'keyword', 'project__name').annotate(
            action=Concat('action__type__name', Value(' - '), 'action__name', output_field=CharField()))
    else:
        objects = Step.objects.filter(q, is_active=True).values('pk', 'name', 'keyword', 'project__name').annotate(
            action=Concat('action__type__name', Value(' - '), 'action__name', output_field=CharField()))
    # 排序
    if objects:
        if order_by not in objects[0]:
            order_by = 'pk'
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
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': {
        'objects': list(objects), 'page': page, 'max_page': paginator.num_pages, 'size': size}})


# 获取临时step
@login_required
def list_temp(request):
    list_ = json.loads(request.POST.get('condition', ''))
    order = 0
    list_temp = list()
    for pk in list_:
        if pk.strip() == '':
            continue
        order += 1
        objects = Step.objects.filter(pk=pk).values('pk', 'name').annotate(
            action=Concat('action__type__name', Value(' - '), 'action__name', output_field=CharField()))
        objects = list(objects)
        objects[0]['order'] = order
        list_temp.append(objects[0])
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': list_temp})


# 复制
@login_required
def copy_(request, pk):
    name = request.POST.get('name', '')
    try:
        obj = Step.objects.get(pk=pk)
        obj.pk = None
        obj.name = name
        obj.creator = obj.modifier = request.user
        obj.clean_fields()
        obj.save()
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': obj.pk})
    except Step.DoesNotExist as e:
        return JsonResponse({'statue': 1, 'message': 'ERROR', 'data': str(e)})
