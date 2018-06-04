import json
import traceback
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render, get_object_or_404
from django.core.serializers import serialize
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db import connection
from django.db.models import Q, F, CharField, Value
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core import serializers
# from django.views.decorators.csrf import csrf_exempt
from main.models import Case, Step, Action, CaseVsStep
from main.forms import PaginatorForm, StepForm, CaseForm


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
    keyword_list_temp = search_text.split(' ')
    keyword_list = list()
    for keyword in keyword_list_temp:
        if keyword.strip() != '':
            keyword_list.append(keyword)
    q = get_query_condition(keyword_list)
    objects = Case.objects.filter(q, is_active=1).order_by('id')
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
    return render(request, 'main/cases.html', locals())


# 用例详情
@login_required
def case(request, pk):
    try:
        obj = Case.objects.select_related('creator', 'modifier').get(pk=pk)
    except Case.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        form = CaseForm(instance=obj)
        if request.GET.get('success', '') == '1' and request.META.get('HTTP_REFERER'):
            is_success = True
        return render(request, 'main/case.html', locals())
    elif request.method == 'POST':
        creator = obj.creator
        form = CaseForm(data=request.POST, instance=obj)
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            step_list = json.loads(request.POST.get('step', ''))
            csv = CaseVsStep.objects.filter(case=obj).order_by('order')
            original_step_list = list()
            for csv_dict in csv.values('step'):
                original_step_list.append(str(csv_dict['step']))
            if original_step_list != step_list:
                csv.delete()
                order = 0
                for step_str in step_list:
                    if step_str.strip() == '':
                        continue
                    order += 1
                    step_ = Step.objects.get(pk=step_str)
                    CaseVsStep.objects.create(case=obj, step=step_, order=order, creator=request.user, modifier=request.user)
            # form.save_m2m()
            return HttpResponseRedirect(reverse('case', args=[pk]) + '?success=1')
    is_success = False
    print(form.errors)
    return render(request, 'main/case.html', locals())


@login_required
def case_add(request):
    if request.method == 'GET':
        form = CaseForm()
        return render(request, 'main/case.html', locals())
    elif request.method == 'POST':
        form = CaseForm(data=request.POST)
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = request.user
            form_.modifier = request.user
            form_.is_active = True
            form_.save()
            form.save_m2m()
            pk = form_.id
            return HttpResponseRedirect(reverse('case', args=[pk]) + '?success=1')
        else:
            return render(request, 'main/case.html', locals())


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


# 生成查询条件的Q对象
def get_query_condition(query_str_list):
    q = Q()
    for query_str in query_str_list:
        query_str = str(query_str)
        q |= Q(name__icontains=query_str) | Q(keyword__icontains=query_str)
    return q


def execute_query(sql):
    cursor = connection.cursor()  # 获得一个游标(cursor)对象
    cursor.execute(sql)
    raw_data = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    result = list()
    for row in raw_data:
        obj_dict = dict()
        # 把每一行的数据遍历出来放到Dict中
        for index, value in enumerate(row):
            obj_dict[col_names[index]] = value
        result.append(obj_dict)
    return result


def run(request):
    return render(request,
                  'automation_test/result/Automation_Test_Report_2017-02-14_115725/Automation_Test_Report_2017-02-14_115725.html')


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
    return render(request, 'main/steps.html', locals())


@login_required
def step(request, pk):
    obj = Step.objects.select_related('creator', 'modifier').get(pk=pk)
    # obj = get_object_or_404(Step, pk=pk).select_related('creator', 'modifier')
    if request.method == 'GET':
        form = StepForm(instance=obj)
        related_objects = obj.case_set.filter(is_active=True)
        if request.GET.get('success', '') == '1' and request.META.get('HTTP_REFERER'):
            is_success = True
        return render(request, 'main/step.html', locals())
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
            return HttpResponseRedirect(reverse('step', args=[pk]) + '?success=1')
    is_success = False
    return render(request, 'main/step.html', locals())


@login_required
def step_add(request):
    if request.method == 'GET':
        form = StepForm()
        return render(request, 'main/step.html', locals())
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
            return HttpResponseRedirect(reverse('step', args=[pk]) + '?success=1')
        else:
            return render(request, 'main/step.html', locals())


@login_required
def step_delete(request, pk):
    if request.method == 'POST':
        Step.objects.filter(pk=pk).update(is_active=0, modifier=request.user, modified_date=timezone.now())
        return HttpResponse('success')
    else:
        return HttpResponseBadRequest('only accept "POST" method')


@login_required
def step_update(request, pk):
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


# 获取action
@login_required
def action_list(request):
    data = json.loads(request.POST['data'])
    objects = Action.objects.filter(is_active=1).order_by('type__id', 'name', 'id').values('id', 'name', 'type__name', 'keyword').select_related()
    for o in objects:
        o['name'] = '{} - {} - {}'.format(o['type__name'], o['name'], o['keyword'])
        if o['id'] in data:
            o['selected'] = True

    data_dict = dict()
    data_dict['data'] = list(objects)
    return JsonResponse(data_dict)


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
    v = Step.objects.filter(is_active=1).order_by('pk').values('pk', 'name').annotate(
        action=Concat('action__name', Value(' - '), 'action__type__name', output_field=CharField()))
    data_dict = dict()
    data_dict['data'] = list(v)
    return JsonResponse(data_dict)


# 获取选中的step
@login_required
def case_steps(request, pk):
    v = Step.objects.filter(case=pk).order_by('casevsstep__order').values(
        'pk', 'name', order=F('casevsstep__order')).annotate(
        action=Concat('action__name', Value(' - '), 'action__type__name', output_field=CharField()))
    data_dict = dict()
    data_dict['data'] = list(v)
    return JsonResponse(data_dict)


def test1(request):
    return render(request, 'main/test1.html')


def test2(request):
    return render(request, 'main/test2.html')


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/cases'))
