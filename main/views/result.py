import os
import json
import logging
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import F, CharField, Value, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import SuiteResult, StepResult
from main.forms import PaginatorForm, SuiteResultForm
from main.views.general import get_query_condition
from django.forms.models import model_to_dict
from manage import PROJECT_ROOT
from py_test.general.execute_suite import execute_suite

logger = logging.getLogger('django.request')


# 用例列表
@login_required
def results(request):
    prompt = None
    if request.method == 'POST':
        page = int(request.POST.get('page', 1)) if request.POST.get('page') != '' else 1
        size = int(request.POST.get('size', 5)) if request.POST.get('size') != '' else 10
        search_text = str(request.POST.get('search_text', ''))
    else:
        page = int(request.COOKIES.get('page', 1))
        size = int(request.COOKIES.get('size', 10))
        search_text = ''
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
    keyword_list_temp = search_text.split(' ')
    keyword_list = list()
    for keyword in keyword_list_temp:
        if keyword.strip() != '':
            keyword_list.append(keyword)
    q = get_query_condition(keyword_list)
    objects = SuiteResult.objects.filter(q, is_active=True).order_by('-start_date').values('pk', 'name', 'keyword', 'start_date', 'result_status')
    result_status_list = SuiteResult.result_status_list
    d = {l[0]: l[1] for l in result_status_list}
    for o in objects:
        o['result_status_str'] = d.get(o['result_status'], 'N/A')
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
    return render(request, 'main/result/list.html', locals())


# 用例详情
@login_required
def result(request, pk):
    try:
        obj = SuiteResult.objects.select_related('creator', 'modifier').get(pk=pk)
    except SuiteResult.DoesNotExist:
        raise Http404('SuiteResult does not exist')
    sub_objects = obj.caseresult_set.all().order_by('case_order')
    if request.method == 'GET':
        form = SuiteResultForm(initial={'name': obj.name, 'description': obj.description, 'keyword': obj.keyword})
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/result/detail.html', locals())
    elif request.method == 'POST':
        creator = obj.creator
        form = SuiteResultForm(data=request.POST)
        if form.is_valid():
            obj.name = form.data['name']
            obj.description = form.data['description']
            obj.keyword = form.data['keyword']
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
def result_add(request):
    if request.method == 'GET':
        form = SuiteForm()
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/suite/detail.html', locals())
    elif request.method == 'POST':
        form = SuiteForm(data=request.POST)
        try:
            m2m_list = json.loads(request.POST.get('case', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            m2m_list = None
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = request.user
            form_.modifier = request.user
            form_.is_active = True
            form_.save()
            # form.save_m2m()
            obj = form_
            pk = obj.id
            if m2m_list:
                order = 0
                for m2m_pk in m2m_list:
                    if m2m_pk.strip() == '':
                        continue
                    order += 1
                    m2m_object = Case.objects.get(pk=m2m_pk)
                    SuiteVsCase.objects.create(suite=obj, case=m2m_object, order=order, creator=request.user,
                                               modifier=request.user)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('suite', args=[pk]) + '?redirect_url=' + redirect_url)
            elif redirect == 'add_another':
                return HttpResponseRedirect(reverse('suite_add') + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        else:
            if m2m_list:
                temp_list_json = json.dumps(m2m_list)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/result/detail.html', locals())


@login_required
def result_delete(request, pk):
    if request.method == 'POST':
        SuiteResult.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


@login_required
def result_quick_update(request, pk):
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
def step_img(request, pk):
    try:
        obj = StepResult.objects.get(pk=pk)
    except StepResult.DoesNotExist:
        raise Http404('StepResult does not exist')
    data_dict = dict()
    data_dict['pk'] = pk
    data_dict['name'] = obj.name
    data_dict['result_message'] = obj.result_message
    data_dict['result_error'] = obj.result_error
    data_dict['start_date'] = obj.start_date
    data_dict['imgs'] = list()
    for img in obj.imgs.all():
        data_dict['imgs'].append(img.img.url)
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': data_dict})
