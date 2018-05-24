import json
import traceback
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render
from django.core.serializers import serialize
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db import connection
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.decorators import login_required
# from django.views.decorators.csrf import csrf_exempt
from main.models import Case, Step, Action
from .forms import PaginatorForm, StepForm


# 用例列表
@login_required
def cases(request):
    pd = dict()
    pd['page'] = int(request.POST.get('page', 1)) if request.POST.get('page') != '' else 1
    pd['size'] = int(request.POST.get('size', 5)) if request.POST.get('size') != '' else 5
    pd['search_input'] = str(request.POST.get('search_input', ''))
    keyword_list_temp = pd['search_input'].split(' ')
    keyword_list = list()
    for keyword in keyword_list_temp:
        if keyword.strip() != '':
            keyword_list.append(keyword)
    q = get_query_condition(keyword_list)
    objects = Case.objects.filter(q, is_valid=1).order_by('name', 'id')
    paginator = Paginator(objects, pd['size'])
    pd['total_page'] = paginator.num_pages
    pd['total_object'] = paginator.count
    try:
        pd['objects'] = paginator.page(pd['page'])
    except PageNotAnInteger:
        pd['objects'] = paginator.page(1)
        pd['page'] = 1
    except EmptyPage:
        pd['objects'] = paginator.page(paginator.num_pages)
        pd['page'] = paginator.num_pages
    return render(request, 'main/cases.html', {'pd': pd})


# 用例详情
@login_required
def case(request):
    pd = dict()
    pd['id'] = str(request.GET.get('id', 0))
    if pd['id'].isdigit():
        pd['id'] = int(float(pd['id']))
    else:
        pd['id'] = 0
    pd['object'] = None
    objects = Case.objects.filter(id=pd['id'])
    if objects:
        pd['object'] = objects[0]
    return render(request, 'main/case.html', {'pd': pd})


def case_delete(request):
    if request.method == 'POST':
        object_id = request.POST.get('object_id')
        if object_id:
            Case.objects.filter(id=object_id).update(is_valid=0, modifier=request.user, modified_date=timezone.now())
        return HttpResponse('success')
    else:
        return HttpResponseBadRequest('only accept "POST" method')


def case_update(request):
    response_ = {'new_value': ''}
    try:
        col_name = request.POST['col_name']
        object_id = int(request.POST['object_id'])
        new_value = request.POST['new_value']
        response_['new_value'] = new_value
        if col_name == 'name':
            Case.objects.filter(id=object_id).update(name=new_value, modifier=request.user,
                                                     modified_date=timezone.now())
        elif col_name == 'keyword':
            Case.objects.filter(id=object_id).update(keyword=new_value, modifier=request.user,
                                                     modified_date=timezone.now())
        else:
            raise ValueError('invalid col_name')
    except Exception as e:
        print(traceback.format_exc())
        return HttpResponseBadRequest(traceback.format_exc())
    return JsonResponse(response_)


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


# 步骤
@login_required
def steps(request):
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
    objects = Step.objects.filter(q, is_valid=1).order_by('id')
    paginator = Paginator(objects, size)
    # pd['total_page'] = paginator.num_pages
    # pd['total_object'] = paginator.count
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
        page = 1
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    paginator_form = PaginatorForm(initial={'page': page, 'size': size})
    return render(request, 'main/steps.html', locals())


@login_required
def step(request, object_id):
    try:
        obj = Step.objects.get(id=object_id)
    except Step.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        form = StepForm(instance=obj)
        if request.GET.get('success', '') == '1' and request.META.get('HTTP_REFERER'):
            is_success = True
        return render(request, 'main/step.html', locals())
    elif request.method == 'POST':
        # 使POST内容可以修改
        # By default QueryDicts are immutable, though the copy() method
        # will always return a mutable copy.
        post = request.POST.copy()
        post['creator'] = str(obj.creator.id)
        post['modifier'] = str(request.user.id)
        post['is_valid'] = str(obj.is_valid)
        form = StepForm(data=post, instance=obj)
        if form.is_valid():
            request.method = 'GET'
            form.save()
            return HttpResponseRedirect(reverse('step', args=[object_id]) + '?success=1')
        else:
            is_success = False
            return render(request, 'main/step.html', locals())


@login_required
def step_add(request):
    if request.method == 'GET':
        form = StepForm()
        return render(request, 'main/step.html', locals())
    elif request.method == 'POST':
        post = request.POST.copy()
        post['creator'] = str(request.user.id)
        post['modifier'] = str(request.user.id)
        post['is_valid'] = '1'
        form = StepForm(data=post)
        if form.is_valid():
            request.method = 'GET'
            object_id = form.save().id
            return HttpResponseRedirect(reverse('step', args=[object_id]) + '?success=1')
        else:
            return render(request, 'main/step.html', locals())


def step_delete(request):
    if request.method == 'POST':
        object_id = request.POST.get('object_id')
        if object_id:
            Step.objects.filter(id=object_id).update(is_valid=0, modifier=request.user, modified_date=timezone.now())
        return HttpResponse('成功')
    else:
        return HttpResponseBadRequest('only accept "POST" method')


def step_update(request):
    response_ = {'new_value': ''}
    try:
        object_id = int(request.POST['object_id'])
        col_name = request.POST['col_name']
        new_value = request.POST['new_value']
        response_['new_value'] = new_value
        if col_name == 'name':
            Step.objects.filter(id=object_id).update(name=new_value, modifier=request.user,
                                                     modified_date=timezone.now())
        elif col_name == 'keyword':
            Step.objects.filter(id=object_id).update(keyword=new_value, modifier=request.user,
                                                     modified_date=timezone.now())
        else:
            raise ValueError('invalid col_name')
    except Exception as e:
        print(traceback.format_exc())
        return HttpResponseBadRequest(traceback.format_exc())
    return JsonResponse(response_)


def step_update_all(request):
    try:
        object_id = request.POST.get('object_id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        keyword = request.POST.get('keyword')
        timeout = request.POST.get('timeout', '')
        if timeout == '':
            timeout = None
        save_as = request.POST.get('save_as')
        ui_by = request.POST.get('ui_by', 0)

        Step.objects.filter(id=object_id).update(
            name=name,
            description=description,
            keyword=keyword,
            timeout=timeout,
            save_as=save_as,
            ui_by=ui_by,
            modifier=request.user, modified_date=timezone.now())

    except Exception as e:
        print(traceback.format_exc())
        return HttpResponseBadRequest(traceback.format_exc())
    return HttpResponseRedirect('{}?id={}'.format(reverse('step'), object_id))


# 获取action
@login_required
def action_list(request):
    data = json.loads(request.POST['data'])
    objects = Action.objects.filter(is_valid=1).order_by('type__id', 'name', 'id').values('id', 'name', 'type__name',
                                                                                          'keyword')
    for o in objects:
        o['name'] = '{} - {} - {}'.format(o['type__name'], o['name'], o['keyword'])
        if o['id'] in data:
            o['selected'] = True

    data_dict = dict()
    data_dict['data'] = list(objects)
    return JsonResponse(data_dict)
