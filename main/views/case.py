import json
import traceback
import sys
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
from main.models import Case, Step, Action, CaseVsStep
from main.forms import PaginatorForm, StepForm, CaseForm
from main.views.general import get_query_condition


# 用例列表
@login_required
def cases(request):
    if request.method == 'POST':
        page = int(request.POST.get('page', 1)) if request.POST.get('page') != '' else 1
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
    # objects = Case.objects.filter(q, is_active=1).order_by('id')
    objects = Case.objects.filter(is_active=1).order_by('id').values('pk', 'name', 'keyword').annotate(
        step_count=Count('step'))
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
    return render(request, 'main/case/list.html', locals())


# 用例详情
@login_required
def case(request, pk):
    try:
        obj = Case.objects.select_related('creator', 'modifier').get(pk=pk)
    except Case.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        form = CaseForm(instance=obj)
        if request.session.get('status', None) == 'success':
            is_success = True
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER'))
        return render(request, 'main/case/detail.html', locals())
    elif request.method == 'POST':
        creator = obj.creator
        form = CaseForm(data=request.POST, instance=obj)
        step_list = json.loads(request.POST.get('step', '[]'))
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            # form.save_m2m()
            cvs = CaseVsStep.objects.filter(case=obj).order_by('order')
            original_step_list = list()
            for csv_dict in cvs.values('step'):
                original_step_list.append(str(csv_dict['step']))
            if original_step_list != step_list:
                cvs.delete()
                order = 0
                for step_str in step_list:
                    if step_str.strip() == '':
                        continue
                    order += 1
                    step_ = Step.objects.get(pk=step_str)
                    CaseVsStep.objects.create(case=obj, step=step_, order=order, creator=request.user, modifier=request.user)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('case', args=[pk]) + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        else:
            # 暂存step列表
            csv = CaseVsStep.objects.filter(case=obj).order_by('order')
            original_step_list = list()
            for csv_dict in csv.values('step'):
                original_step_list.append(str(csv_dict['step']))
            temp_list = list()
            temp_dict = dict()
            if original_step_list != step_list:
                temp_list_json = json.dumps(step_list)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/case/detail.html', locals())


@login_required
def case_add(request):
    if request.method == 'GET':
        form = CaseForm()
        if request.session.get('status', None) == 'success':
            is_success = True
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER'))
        return render(request, 'main/case/detail.html', locals())
    elif request.method == 'POST':
        form = CaseForm(data=request.POST)
        step_list = json.loads(request.POST.get('step', '[]'))
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = request.user
            form_.modifier = request.user
            form_.is_active = True
            form_.save()
            # form.save_m2m()
            obj = form_
            pk = obj.id
            order = 0
            for step_str in step_list:
                if step_str.strip() == '':
                    continue
                order += 1
                step_ = Step.objects.get(pk=step_str)
                CaseVsStep.objects.create(case=obj, step=step_, order=order, creator=request.user,
                                          modifier=request.user)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('case', args=[pk]) + '?redirect_url=' + redirect_url)
            elif redirect == 'add_another':
                return HttpResponseRedirect(reverse('case_add') + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        else:
            temp_list_json = json.dumps(step_list)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/case/detail.html', locals())


@login_required
def case_delete(request, pk):
    if request.method == 'POST':
        Case.objects.filter(pk=pk).update(is_active=0, modifier=request.user, modified_date=timezone.now())
        return HttpResponse('success')
    else:
        return HttpResponseBadRequest('only accept "POST" method')


@login_required
def case_update(request, pk):
    if request.method == 'POST':
        response_ = {'new_value': ''}
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            response_['new_value'] = new_value
            obj = Case.objects.get(pk=pk)
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


# 获取选中的step
@login_required
def case_steps(request, pk):
    v = Step.objects.filter(case=pk).order_by('casevsstep__order').values(
        'pk', 'name', order=F('casevsstep__order')).annotate(
        action=Concat('action__name', Value(' - '), 'action__type__name', output_field=CharField()))
    data_dict = dict()
    data_dict['data'] = list(v)
    return JsonResponse(data_dict)


# 获取临时step
@login_required
def step_list_temp(request):
    step_list = json.loads(request.POST.get('condition', ''))
    order = 0
    list_ = list()
    for step_str in step_list:
        if step_str.strip() == '':
            continue
        order += 1
        step_ = Step.objects.filter(pk=step_str).values('pk', 'name').annotate(
            action=Concat('action__name', Value(' - '), 'action__type__name', output_field=CharField()))
        step_ = list(step_)
        step_[0]['order'] = order
        list_.append(step_[0])
    data_dict = dict()
    data_dict['data'] = list_
    return JsonResponse(data_dict)
