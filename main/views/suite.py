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
from main.models import Suite, Case, SuiteVsCase
from main.forms import PaginatorForm, SuiteForm
from main.views.general import get_query_condition
from django.forms.models import model_to_dict
from manage import PROJECT_ROOT
from py_test.general.execute_suite import execute_suite

logger = logging.getLogger('django.request')


# 用例列表
@login_required
def suites(request):
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
    objects = Suite.objects.filter(q, is_active=True).order_by('id').values('pk', 'name', 'keyword', 'config__name')
    objects2 = Suite.objects.filter(is_active=True, case__is_active=True).values('pk').annotate(m2m_count=Count('case'))
    count_ = {o['pk']: o['m2m_count'] for o in objects2}
    for o in objects:
        o['m2m_count'] = count_.get(o['pk'], 0)
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
    return render(request, 'main/suite/list.html', locals())


# 用例详情
@login_required
def suite(request, pk):
    try:
        obj = Suite.objects.select_related('creator', 'modifier').get(pk=pk)
    except Suite.DoesNotExist:
        raise Http404('Suite does not exist')
    if request.method == 'GET':
        form = SuiteForm(instance=obj)
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/suite/detail.html', locals())
    elif request.method == 'POST':
        creator = obj.creator
        form = SuiteForm(data=request.POST, instance=obj)
        try:
            m2m_list = json.loads(request.POST.get('case', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            m2m_list = None
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            # form.save_m2m()
            if m2m_list:
                m2m = SuiteVsCase.objects.filter(suite=obj).order_by('order')
                original_m2m_list = list()
                for dict_ in m2m.values('case'):
                    original_m2m_list.append(str(dict_['case']))
                if original_m2m_list != m2m_list:
                    m2m.delete()
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
            else:
                return HttpResponseRedirect(redirect_url)
        else:
            if m2m_list:
                # 暂存step列表
                m2m = SuiteVsCase.objects.filter(suite=obj).order_by('order')
                original_m2m_list = list()
                for dict_ in m2m.values('case'):
                    original_m2m_list.append(str(dict_['case']))
                temp_list = list()
                temp_dict = dict()
                if original_m2m_list != m2m_list:
                    temp_list_json = json.dumps(m2m_list)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/suite/detail.html', locals())


@login_required
def suite_add(request):
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
        return render(request, 'main/suite/detail.html', locals())


@login_required
def suite_delete(request, pk):
    if request.method == 'POST':
        Suite.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


@login_required
def suite_quick_update(request, pk):
    if request.method == 'POST':
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            obj = Suite.objects.get(pk=pk)
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


# 获取选中的case
@login_required
def suite_cases(request, pk):
    objects = Case.objects.filter(suite=pk, is_active=True).order_by('suitevscase__order').values('pk', 'name', order=F('suitevscase__order'))
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': list(objects)})


# 获取临时case
@login_required
def case_list_temp(request):
    list_ = json.loads(request.POST.get('condition', ''))
    order = 0
    list_temp = list()
    for pk in list_:
        if pk.strip() == '':
            continue
        order += 1
        objects = Case.objects.filter(pk=pk).values('pk', 'name').annotate(
            action=Concat('action__name', Value(' - '), 'action__type__name', output_field=CharField()))
        objects = list(objects)
        objects[0]['order'] = order
        list_temp.append(objects[0])
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': list_temp})


# 执行套件
@login_required
def suite_execute(request, pk):
    try:
        suite_ = Suite.objects.get(pk=pk, is_active=True)
        result_path = os.path.join(PROJECT_ROOT, 'test_result')
        suite_result = execute_suite(request, suite_, result_path)
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': model_to_dict(suite_result)})
    except Suite.DoesNotExist:
        return JsonResponse({'statue': 2, 'message': 'Suite does not exist', 'data': None})
