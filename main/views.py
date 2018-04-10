import json
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.core.serializers import serialize
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import connection
from django.db.models import Q
from django.utils import timezone
# from django.views.decorators.csrf import csrf_exempt
from main.models import Case


def list_case(request):
    if request.user.is_authenticated:
        # query_set = Case.objects.filter(is_valid=1).select_related('tcg').order_by('tcg', 'order')
        # query_set = Case.objects.filter(is_valid=1).order_by('name')
        pd = dict()
        pd['page'] = int(request.POST.get('page', 1)) if request.POST.get('page') != '' else 1
        pd['size'] = int(request.POST.get('size', 3)) if request.POST.get('size') != '' else 3
        pd['search_input'] = str(request.POST.get('search_input', ''))
        keyword_list_temp = pd['search_input'].split(' ')
        keyword_list = list()
        for keyword in keyword_list_temp:
            if keyword.strip() != '':
                keyword_list.append(keyword)
        q = get_query_condition(keyword_list)
        case_list = Case.objects.filter(q, is_valid=1)
        paginator = Paginator(case_list, pd['size'])
        try:
            cases = paginator.page(pd['page'])
        except PageNotAnInteger:
            cases = paginator.page(1)
        except EmptyPage:
            cases = paginator.page(paginator.num_pages)
        return render(request, 'main/case_list.html', {'cases': cases, 'pd': pd})
    else:
        return HttpResponseRedirect('/admin/login/?next=/tc_list/')


def delete_case(request):
    if request.method == 'POST':
        data_id = request.POST.get('data_id')
        if data_id:
            Case.objects.filter(id=data_id).update(is_valid=0, modifier=request.user.username, modified_date=timezone.now())
        return HttpResponseRedirect('/list_case/')
    else:
        return HttpResponseBadRequest('only accept "POST" method')


def update_case(request):
    response_ = {'new_value': ''}
    try:
        col_name = request.POST['col_name']
        data_id = int(request.POST['data_id'])
        new_value = request.POST['new_value']
        response_['new_value'] = new_value
        if col_name == 'name':
            Case.objects.filter(id=data_id).update(name=new_value, modifier=request.user.username,
                                                   modified_date=timezone.now())
        elif col_name == 'keyword':
            Case.objects.filter(id=data_id).update(keyword=new_value, modifier=request.user.username,
                                                   modified_date=timezone.now())
        else:
            raise ValueError('invalid col_name')
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    return JsonResponse(response_)


def delete_case1(request):
    try:
        data_id = int(request.POST['data_id'])
        Case.objects.filter(id=data_id).update(is_valid=0, modifier=request.user.username,
                                               modified_date=timezone.now())
        cases = Case.objects.filter(is_valid=1).order_by('name')
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    return render(request, 'main/tc_list_tr.html', {'cases': cases})


def tc_pagination(request):
    search_criteria = request.POST['search_criteria']
    is_valid = [True, ]
    name = ''
    keyword_list = []
    start_index = 0
    page_size_ = 3
    end_index = start_index + page_size_
    if name == '':
        nq = Q()
    else:
        nq = Q(name__icontains=name)
    kq = keyword_query(keyword_list)
    query_set = Case.objects.filter(kq, nq, is_valid__in=is_valid).order_by('name')[start_index:end_index]
    return render(request, 'main/tc_list_tr.html', {'query_set': query_set})


def get_tc_list(request):
    is_valid = [True, ]
    name = ''
    keyword_list = ['TEST']
    start_index = 0
    page_size_ = 3
    end_index = start_index + page_size_
    if name == '':
        nq = Q()
    else:
        nq = Q(name__icontains=name)
    kq = keyword_query(keyword_list)
    query_set = Case.objects.filter(kq, nq, is_valid__in=is_valid).order_by('name')[start_index:end_index]
    # ===========================================================================
    # for v in query_set:
    #     v.created_date = v.created_date.astimezone(datetime.timezone(datetime.timedelta(hours=8)))#.strftime('%Y-%m-%d %H:%M:%S.%f')
    #     v.modified_date = v.modified_date.astimezone(datetime.timezone(datetime.timedelta(hours=8)))#.strftime('%Y-%m-%d %H:%M:%S.%f')
    # ===========================================================================
    json_ = serialize('json', query_set, use_natural_foreign_keys=True)
    print(json_)
    obj = json.loads(json_)
    return JsonResponse(obj, safe=False)


def keyword_query(keyword_list):
    kq = Q()
    for keyword in keyword_list:
        keyword = str(keyword)
        kq |= (
                Q(keyword__iregex='^' + keyword + '$') |
                Q(keyword__iregex='^' + keyword + '\s') |
                Q(keyword__iregex='\s' + keyword + '$') |
                Q(keyword__iregex='\s' + keyword + '\s')
        )
    return kq


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
    result = []
    for row in raw_data:
        obj_dict = {}
        # 把每一行的数据遍历出来放到Dict中
        for index, value in enumerate(row):
            obj_dict[col_names[index]] = value
        result.append(obj_dict)
    return result


def run(request):
    return render(request,
                  'automation_test/result/Automation_Test_Report_2017-02-14_115725/Automation_Test_Report_2017-02-14_115725.html')
