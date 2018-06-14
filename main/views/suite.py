import json
import traceback
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
    objects = Suite.objects.filter(q, is_active=True).order_by('id').values('pk', 'name', 'keyword', 'config__name').annotate(m2m_count=Count('case'))
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
        raise Http404('Step does not exist')
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
        m2m_list = json.loads(request.POST.get('case', '[]'))
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            # form.save_m2m()
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
        m2m_list = json.loads(request.POST.get('case', '[]'))
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
            temp_list_json = json.dumps(m2m_list)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/suite/detail.html', locals())


@login_required
def suite_delete(request, pk):
    if request.method == 'POST':
        Suite.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return HttpResponse('success')
    else:
        return HttpResponseBadRequest('only accept "POST" method')


@login_required
def suite_quick_update(request, pk):
    if request.method == 'POST':
        response_ = {'new_value': ''}
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            response_['new_value'] = new_value
            obj = Suite.objects.get(pk=pk)
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


# 获取选中的case
@login_required
def suite_cases(request, pk):
    v = Case.objects.filter(suite=pk, is_active=True).order_by('suitevscase__order').values('pk', 'name', order=F('suitevscase__order'))
    data_dict = dict()
    data_dict['data'] = list(v)
    return JsonResponse(data_dict)


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
    data_dict = dict()
    data_dict['data'] = list_temp
    return JsonResponse(data_dict)


# 执行套件
@login_required
def suite_execute(request, pk):
    from py_test.general.execute_suite import execute_suite
    suite_result = execute_suite(request, pk, 'result1111')
    return JsonResponse(model_to_dict(suite_result))