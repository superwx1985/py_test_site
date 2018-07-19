import json
import logging
import copy
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import Q, F, CharField, Value, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import Suite, Case, SuiteVsCase
from main.forms import OrderByForm, PaginatorForm, SuiteForm
from main.views.general import get_query_condition, change_to_positive_integer, Cookie
from py_test.general.execute_suite import execute_suite
from django.template.loader import render_to_string
from urllib.parse import quote
from main.views import case

logger = logging.getLogger('django.request')


# 列表
@login_required
def list_(request):
    page = request.GET.get('page')
    size = request.GET.get('size', request.COOKIES.get('size'))
    search_text = str(request.GET.get('search_text', ''))
    order_by = request.GET.get('order_by', 'modified_date')
    order_by_reverse = request.GET.get('order_by_reverse', 'True')
    all_ = request.GET.get('all_', 'False')

    page = change_to_positive_integer(page, 1)
    size = change_to_positive_integer(size, 10)
    if order_by_reverse == 'True':
        order_by_reverse = True
    else:
        order_by_reverse = False
    if all_ == 'False':
        all_ = False
    else:
        all_ = True

    if request.session.get('status', None) == 'success':
        prompt = 'success'
    request.session['status'] = None
    q = get_query_condition(search_text)
    if all_:
        q &= Q(is_active=True)
    else:
        q &= Q(is_active=True) & Q(creator=request.user)
    objects = Suite.objects.filter(q).values(
        'pk', 'name', 'keyword', 'project__name', 'config__name', 'creator', 'creator__username', 'modified_date')
    objects2 = Suite.objects.filter(is_active=True, case__is_active=True).values('pk').annotate(m2m_count=Count('case'))
    count_ = {o['pk']: o['m2m_count'] for o in objects2}
    for o in objects:
        o['m2m_count'] = count_.get(o['pk'], 0)
    # 排序
    if objects:
        if order_by not in objects[0]:
            order_by = 'modified_date'
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
    # 设置cookie
    cookies = [Cookie('size', size, path=request.path)]
    respond = render(request, 'main/suite/list.html', locals())
    for cookie in cookies:
        respond.set_cookie(cookie.key, cookie.value, cookie.max_age, cookie.expires, cookie.path)
    return respond


# 详情
@login_required
def detail(request, pk):
    next_ = request.GET.get('next', '/home/')
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
        obj_temp = copy.deepcopy(obj)
        form = SuiteForm(data=request.POST, instance=obj_temp)
        try:
            m2m_list = json.loads(request.POST.get('case', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            m2m_list = None
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = obj.creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            # form.save_m2m()
            if m2m_list is not None:
                m2m = SuiteVsCase.objects.filter(suite=obj).order_by('order')
                original_m2m_list = list()
                for dict_ in m2m.values('case'):
                    original_m2m_list.append(str(dict_['case']))
                if original_m2m_list != m2m_list:
                    m2m.delete()
                    order = 0
                    for m2m_pk in m2m_list:
                        if m2m_pk is None or m2m_pk.strip() == '':
                            continue
                        try:
                            m2m_obj = Case.objects.get(pk=m2m_pk)
                        except Case.DoesNotExist:
                            logger.warning('找不到m2m对象[{}]'.format(m2m_pk), exc_info=True)
                            continue
                        order += 1
                        SuiteVsCase.objects.create(suite=obj, case=m2m_obj, order=order, creator=request.user,
                                                   modifier=request.user)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            if redirect:
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect(request.get_full_path())
        else:
            if m2m_list is not None:
                # 暂存step列表
                m2m = SuiteVsCase.objects.filter(suite=obj).order_by('order')
                original_m2m_list = list()
                for dict_ in m2m.values('case'):
                    original_m2m_list.append(str(dict_['case']))
                temp_list = list()
                temp_dict = dict()
                if original_m2m_list != m2m_list:
                    temp_list_json = json.dumps(m2m_list)

        is_success = False
        return render(request, 'main/suite/detail.html', locals())


@login_required
def add(request):
    next_ = request.GET.get('next', '/home/')
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
            if m2m_list is not None:
                order = 0
                for m2m_pk in m2m_list:
                    if m2m_pk is None or m2m_pk.strip() == '':
                        continue
                    try:
                        m2m_obj = Case.objects.get(pk=m2m_pk)
                    except Case.DoesNotExist:
                        logger.warning('找不到m2m对象[{}]'.format(m2m_pk), exc_info=True)
                        continue
                    order += 1
                    SuiteVsCase.objects.create(suite=obj, case=m2m_obj, order=order, creator=request.user,
                                               modifier=request.user)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            if redirect == 'add_another':
                return HttpResponseRedirect(request.get_full_path())
            elif redirect:
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect('{}?next={}'.format(reverse(detail, args=[pk]), quote(next_)))
        else:
            if m2m_list is not None:
                temp_list_json = json.dumps(m2m_list)

        is_success = False
        return render(request, 'main/suite/detail.html', locals())


@login_required
def delete(request, pk):
    if request.method == 'POST':
        Suite.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


@login_required
def quick_update(request, pk):
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
def cases(_, pk):
    objects = Case.objects.filter(suite=pk, is_active=True).order_by('suitevscase__order').values(
        'pk', 'name', 'keyword', 'project__name', order=F('suitevscase__order'))
    for obj in objects:
        obj['url'] = reverse(case.detail, args=[obj['pk']])
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
def execute_(request, pk):
    try:
        suite_ = Suite.objects.get(pk=pk, is_active=True)
        suite_result = execute_suite(request, suite_)
        sub_objects = suite_result.caseresult_set.filter(step_result=None).order_by('case_order')
        suite_result_content = render_to_string('main/include/suite_result_content.html', locals())
        data_dict = dict()
        data_dict['suite_result_content'] = suite_result_content
        data_dict['suite_result_url'] = reverse('result', args=[suite_result.pk])
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': data_dict})
    except Suite.DoesNotExist:
        return JsonResponse({'statue': 2, 'message': 'Suite does not exist', 'data': None})
