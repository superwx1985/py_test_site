import json
import traceback
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest
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
    objects = Step.objects.filter(q, is_valid=1).order_by('name', 'id')
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
    return render(request, 'main/steps.html', {'pd': pd})


@login_required
def step(request, object_id, is_success=None):
    from .forms import StepForm
    # 当post时，提交表单
    if request.method == 'POST':
        form = StepForm(request.POST)
        try:
            if not form.is_valid():
                is_success = False
                return render(request, 'main/step.html', locals())
                # return render(request, reverse('step', args=(object_id,)), locals())
            name = form.data.get('name')
            description = form.data.get('description')
            keyword = form.data.get('keyword')
            action = form.data.get('action')
            timeout = form.data.get('timeout')
            if timeout == '':
                timeout = None
            save_as = form.data.get('save_as')
            ui_by = form.data.get('ui_by')
            ui_locator = form.data.get('ui_locator')
            ui_index = form.data.get('ui_index')
            if ui_index == '':
                ui_index = None
            ui_base_element = form.data.get('ui_base_element')
            ui_data = form.data.get('ui_data')
            ui_special_action = form.data.get('ui_special_action')
            ui_alert_handle = form.data.get('ui_alert_handle')
            api_url = form.data.get('api_url')
            api_headers = form.data.get('api_headers')
            api_body = form.data.get('api_body')
            api_data = form.data.get('api_data')

            Step.objects.filter(id=object_id).update(
                name=name,
                description=description,
                keyword=keyword,
                action=action,
                timeout=timeout,
                save_as=save_as,
                ui_by=ui_by,
                ui_locator=ui_locator,
                ui_index=ui_index,
                ui_base_element=ui_base_element,
                ui_data=ui_data,
                ui_special_action=ui_special_action,
                ui_alert_handle=ui_alert_handle,
                api_url=api_url,
                api_headers=api_headers,
                api_body=api_body,
                api_data=api_data,
                modifier=request.user, modified_date=timezone.now())

        except Exception as e:
            print(traceback.format_exc())
            return HttpResponseBadRequest(traceback.format_exc())
        # return render(request, 'main/step.html', locals())
        # 为保证数据一致，重新取一次数据库中的值
        request.method = 'GET'
        return step(request, object_id, is_success=True)
    # 当不是post时，展示数据
    else:
        object_ = dict()
        objects = Step.objects.filter(id=object_id)
        # 如果id存在
        if objects:
            object_ = objects[0]
            form = StepForm(initial={
                'id': object_id,
                'name': object_.name,
                'description': object_.description,
                'keyword': object_.keyword,
                # 'action_id': object_.action_id,
                'action': object_.action,
                'timeout': object_.timeout,
                'save_as': object_.save_as,
                'ui_by': object_.ui_by,
                'ui_locator': object_.ui_locator,
                'ui_index': object_.ui_index,
                'ui_base_element': object_.ui_base_element,
                'ui_data': object_.ui_data,
                'ui_special_action': object_.ui_special_action,
                'ui_alert_handle': object_.ui_alert_handle,
                'api_url': object_.api_url,
                'api_headers': object_.api_headers,
                'api_body': object_.api_body,
                'api_data': object_.api_data,
            })
            return render(request, 'main/step.html', locals())
        # 如果id不存在则返回404
        else:
            return HttpResponseBadRequest('404')


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
