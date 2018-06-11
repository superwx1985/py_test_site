import json
import traceback
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
from main.forms import PaginatorForm, StepForm
from main.views.general import get_query_condition


# 步骤列表
@login_required
def steps(request):
    if request.method == 'POST':
        page = int(request.POST.get('page', 1)) if request.POST.get('page') != '' else 1
        if page <= 0:
            page = 1
        size = int(request.POST.get('size', 5)) if request.POST.get('size') != '' else 10
        search_text = str(request.POST.get('search_text', ''))
    else:
        page = int(request.COOKIES.get('page', 1))
        size = int(request.COOKIES.get('size', 10))
        search_text = ''
        if request.session.get('status', None) == 'success':
            is_success = True
        request.session['status'] = None
    keyword_list_temp = search_text.split(' ')
    keyword_list = list()
    for keyword in keyword_list_temp:
        if keyword.strip() != '':
            keyword_list.append(keyword)
    q = get_query_condition(keyword_list)
    # 使用join的方式把多个model结合起来
    objects = Step.objects.filter(q, is_active=1).order_by('id').select_related('action__type')
    # 分割为多条SQL，然后把结果集用python结合起来
    # objects = Step.objects.filter(q, is_active=1).order_by('id').prefetch_related('action__type')
    # 两者结合使用
    # objects = Step.objects.filter(q, is_active=1).order_by('id').select_related('action').prefetch_related(
    #     'action__type')
    paginator = Paginator(objects, size)
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
        page = 1
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    paginator_form = PaginatorForm(initial={'page': page, 'size': size}, page_max_value=paginator.num_pages)
    return render(request, 'main/step/list.html', locals())


@login_required
def step(request, pk):
    try:
        obj = Step.objects.select_related('creator', 'modifier').get(pk=pk)
    except Step.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        related_objects = obj.case_set.filter(is_active=True)
        form = StepForm(instance=obj)
        if request.session.get('status', None) == 'success':
            is_success = True
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER'))
        return render(request, 'main/step/detail.html', locals())
    elif request.method == 'POST':
        creator = obj.creator
        form = StepForm(data=request.POST, instance=obj)
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = creator
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
def step_add(request):
    if request.method == 'GET':
        form = StepForm()
        if request.session.get('status', None) == 'success':
            is_success = True
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER'))
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
def step_delete(request, pk):
    if request.method == 'POST':
        Step.objects.filter(pk=pk).update(is_active=0, modifier=request.user, modified_date=timezone.now())
        return HttpResponse('success')
    else:
        return HttpResponseBadRequest('only accept "POST" method')


@login_required
def step_quick_update(request, pk):
    if request.method == 'POST':
        response_ = {'new_value': ''}
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            response_['new_value'] = new_value
            obj = Step.objects.get(pk=pk)
            obj.modifier = request.user
            obj.modified_date = timezone.now()
            if col_name == 'name':
                obj.name = new_value
                obj.clean_fields()
                obj.save()
            elif col_name == 'keyword':
                obj.keyword = new_value
                obj.clean_fields()
                obj.save()
            else:
                raise ValueError('invalid col_name')
        except Exception as e:
            print(traceback.format_exc())
            return HttpResponseBadRequest(str(e))
        return JsonResponse(response_)
    else:
        return HttpResponseBadRequest('only accept "POST" method')


# 获取全部step
@login_required
def step_list_all_old(request):
    objects = Step.objects.filter(is_active=1).order_by('id').select_related(
        'action', 'creator', 'modifier', 'action__type')
    json_ = serializers.serialize('json', objects, use_natural_foreign_keys=True)
    data_dict = dict()
    data_dict['data'] = json_
    return JsonResponse(data_dict)


# 获取全部step
@login_required
def step_list_all(request):
    objects = Step.objects.filter(is_active=1).order_by('pk').values('pk', 'name').annotate(
        action=Concat('action__name', Value(' - '), 'action__type__name', output_field=CharField()))
    data_dict = dict()
    data_dict['data'] = list(objects)
    return JsonResponse(data_dict)


# 获取临时step
@login_required
def step_list_temp(request):
    list_ = json.loads(request.POST.get('condition', ''))
    order = 0
    list_temp = list()
    for pk in list_:
        if pk.strip() == '':
            continue
        order += 1
        objects = Step.objects.filter(pk=pk).values('pk', 'name').annotate(
            action=Concat('action__name', Value(' - '), 'action__type__name', output_field=CharField()))
        objects = list(objects)
        objects[0]['order'] = order
        list_temp.append(objects[0])
    data_dict = dict()
    data_dict['data'] = list_temp
    return JsonResponse(data_dict)
