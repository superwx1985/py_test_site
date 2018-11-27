import json
import logging
import copy
import uuid
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import Q, F, CharField, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import Suite, Case, SuiteVsCase
from main.forms import OrderByForm, PaginatorForm, SuiteForm
from utils.other import get_query_condition, change_to_positive_integer, Cookie, get_project_list, check_admin
from py_test.general.execute_suite import execute_suite
from django.template.loader import render_to_string
from urllib.parse import quote
from main.views import case, config, variable_group, element_group

logger = logging.getLogger('django.request')


# 列表
@login_required
def list_(request):
    if request.session.get('status', None) == 'success':
        prompt = 'success'
    request.session['status'] = None

    project_list = get_project_list()
    has_sub_object = True
    is_admin = check_admin(request.user)

    page = request.GET.get('page')
    size = request.GET.get('size', request.COOKIES.get('size'))
    search_text = request.GET.get('search_text', '')
    order_by = request.GET.get('order_by', 'pk')
    order_by_reverse = request.GET.get('order_by_reverse', 'True')
    all_ = request.GET.get('all_', 'False')
    search_project = request.GET.get('search_project', None)

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
    if search_project in ('', 'None'):
        search_project = None

    q = get_query_condition(search_text)
    q &= Q(is_active=True)
    if not all_:
        q &= Q(creator=request.user)
    if search_project:
        q &= Q(project=search_project)

    objects = Suite.objects.filter(q).values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'config__name', 'creator', 'creator__username',
        'modified_date').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    m2m_objects = Suite.objects.filter(is_active=True, case__is_active=True).values('pk').annotate(
        m2m_count=Count('case'))
    m2m_count = {o['pk']: o['m2m_count'] for o in m2m_objects}
    result_objects = Suite.objects.filter(is_active=True, suiteresult__is_active=True).values('pk').annotate(
        result_count=Count('suiteresult'))
    result_count = {o['pk']: o['result_count'] for o in result_objects}
    for o in objects:
        o['m2m_count'] = m2m_count.get(o['pk'], 0)
        o['result_count'] = result_count.get(o['pk'], 0)
    # 排序
    if objects:
        if order_by not in objects[0]:
            order_by = 'pk'
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
    inside = request.GET.get('inside')
    new_pk = request.GET.get('new_pk')
    project_list = get_project_list()
    has_sub_object = True
    is_admin = check_admin(request.user)

    try:
        obj = Suite.objects.select_related('creator', 'modifier').get(pk=pk)
    except Suite.DoesNotExist:
        raise Http404('Suite does not exist')

    if request.method == 'POST' and (is_admin or request.user == obj.creator):
        obj_temp = copy.deepcopy(obj)
        form = SuiteForm(data=request.POST, instance=obj_temp)
        try:
            m2m_list = json.loads(request.POST.get('case', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            m2m_list = None
        if form.is_valid():
            obj_temp = form.save(commit=False)
            obj_temp.modifier = request.user
            obj_temp.save()
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

        return render(request, 'main/suite/detail.html', locals())
    else:
        form = SuiteForm(instance=obj)
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        return render(request, 'main/suite/detail.html', locals())


@login_required
def add(request):
    next_ = request.GET.get('next', '/home/')
    inside = request.GET.get('inside')
    project_list = get_project_list()

    if request.method == 'POST':
        form = SuiteForm(data=request.POST)
        try:
            m2m_list = json.loads(request.POST.get('case', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            m2m_list = None
        if form.is_valid():
            obj_temp = form.save(commit=False)
            obj_temp.creator = obj_temp.modifier = request.user
            obj_temp.save()
            obj = obj_temp
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
                # 如果是内嵌网页，则加上内嵌标志后再跳转
                para = ''
                if inside:
                    para = '&inside=1&new_pk={}'.format(pk)
                return HttpResponseRedirect('{}?next={}{}'.format(reverse(detail, args=[pk]), quote(next_), para))
        else:
            if m2m_list is not None:
                temp_list_json = json.dumps(m2m_list)

        return render(request, 'main/suite/detail.html', locals())
    else:
        form = SuiteForm()
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        return render(request, 'main/suite/detail.html', locals())


@login_required
def delete(request, pk):
    err = None
    if request.method == 'POST':
        try:
            obj = Suite.objects.select_related('creator', 'modifier').get(pk=pk)
        except Suite.DoesNotExist:
            err = '对象不存在'
        else:
            is_admin = check_admin(request.user)
            if is_admin or obj.creator == request.user:
                obj.is_active = False
                obj.modifier = request.user
                obj.save()
            else:
                err = '无权限'
    else:
        err = '无效请求'

    if err:
        return JsonResponse({'status': 2, 'message': err, 'data': pk})
    else:
        return JsonResponse({'status': 1, 'message': 'OK', 'data': pk})


@login_required
def multiple_delete(request):
    if request.method == 'POST':
        try:
            pk_list = json.loads(request.POST['pk_list'])
            is_admin = check_admin(request.user)
            if is_admin:
                Suite.objects.filter(pk__in=pk_list).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
            else:
                Suite.objects.filter(pk__in=pk_list, creator=request.user).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
        except Exception as e:
            return JsonResponse({'status': 2, 'message': str(e), 'data': None})
        return JsonResponse({'status': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'status': 2, 'message': 'Only accept "POST" method', 'data': []})


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
            return JsonResponse({'status': 2, 'message': str(e), 'data': None})
        return JsonResponse({'status': 1, 'message': 'OK', 'data': new_value})
    else:
        return JsonResponse({'status': 2, 'message': 'Only accept "POST" method', 'data': None})


# 获取带搜索信息的下拉列表数据
@login_required
def select_json(request):
    condition = request.POST.get('condition', '{}')
    try:
        condition = json.loads(condition)
    except json.decoder.JSONDecodeError:
        condition = dict()
    selected_pk = condition.get('selected_pk')
    url_format = condition.get('url_format')
    url_replacer = condition.get('url_replacer')
    objects = Suite.objects.filter(is_active=True).values('pk', 'name', 'keyword', 'project__name')

    data = list()
    for obj in objects:
        d = dict()
        d['id'] = str(obj['pk'])
        d['name'] = '{} | {}'.format(obj['name'], obj['project__name'])
        d['search_info'] = '{} {} {}'.format(obj['name'], obj['project__name'], obj['keyword'])
        if str(obj['pk']) == selected_pk:
            d['selected'] = True
        else:
            d['selected'] = False
        if url_format and url_replacer:
            url = str.replace(url_format, url_replacer, reverse(detail, args=[obj['pk']]))
        else:
            url = '{}?next={}'.format(reverse(detail, args=[obj['pk']]), reverse(list_))
        d['url'] = url
        data.append(d)

    return JsonResponse({'status': 1, 'message': 'OK', 'data': data})


# 复制操作
def copy_action(pk, user, copy_sub_item, name_prefix=None):
    obj = Suite.objects.get(pk=pk)
    m2m_objects = obj.case.filter(is_active=True).order_by('suitevscase__order')
    obj.pk = None
    if name_prefix:
        obj.name = name_prefix + obj.name
        if len(obj.name) > 100:
            obj.name = obj.name[0:97] + '...'

    copied_items = [dict()]
    if copy_sub_item:
        if obj.config:
            new_sub_obj = config.copy_action(obj.config.pk, user, name_prefix)
            copied_items[0][obj.config] = new_sub_obj
            obj.config = new_sub_obj
        if obj.variable_group:
            new_sub_obj = variable_group.copy_action(obj.variable_group.pk, user, name_prefix)
            copied_items[0][obj.variable_group] = new_sub_obj
            obj.variable_group = new_sub_obj
        if obj.element_group:
            new_sub_obj = element_group.copy_action(obj.element_group.pk, user, name_prefix)
            copied_items[0][obj.element_group] = new_sub_obj
            obj.element_group = new_sub_obj
    obj.creator = obj.modifier = user
    obj.uuid = uuid.uuid1()
    obj.clean_fields()
    obj.save()

    m2m_order = 0
    for m2m_obj in m2m_objects:
        # 判断是否需要复制子对象
        if copy_sub_item:
            # 判断子对象是否已被复制
            if m2m_obj in copied_items[0]:
                m2m_obj_ = copied_items[0][m2m_obj]
            else:
                m2m_obj_ = case.copy_action(m2m_obj.pk, user, copy_sub_item, name_prefix, copied_items)
                copied_items[0][m2m_obj] = m2m_obj_
                # 合并已复制对象字典，并放入容器
                # if copied_items and isinstance(copied_items, list):
                #     copied_items_dict = {**copied_items_dict, **copied_items[0]}
                #     copied_items.clear()
                #     copied_items.append(copied_items_dict)
        else:
            m2m_obj_ = m2m_obj
        m2m_order += 1
        SuiteVsCase.objects.create(
            suite=obj, case=m2m_obj_, order=m2m_order, creator=user, modifier=user)
    return obj


# 复制
@login_required
def copy_(request, pk):
    name_prefix = request.POST.get('name_prefix', '')
    order = request.POST.get('order')
    order = change_to_positive_integer(order, 0)
    copy_sub_item = request.POST.get('copy_sub_item')
    try:
        obj = copy_action(pk, request.user, copy_sub_item, name_prefix)
        return JsonResponse({
            'status': 1, 'message': 'OK', 'data': {
                'new_pk': obj.pk, 'new_url': reverse(detail, args=[obj.pk]), 'order': order}
        })
    except Exception as e:
        return JsonResponse({'status': 2, 'message': str(e), 'data': None})


# 批量复制
@login_required
def multiple_copy(request):
    if request.method == 'POST':
        try:
            pk_list = json.loads(request.POST['pk_list'])
            name_prefix = request.POST.get('name_prefix', '')
            copy_sub_item = request.POST.get('copy_sub_item')
            for pk in pk_list:
                _ = copy_action(pk, request.user, copy_sub_item, name_prefix)
        except Exception as e:
            return JsonResponse({'status': 2, 'message': str(e), 'data': None})
        return JsonResponse({'status': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'status': 2, 'message': 'Only accept "POST" method', 'data': []})


# 获取选中的case
@login_required
def cases(_, pk):
    objects = Case.objects.filter(suite=pk, is_active=True).order_by('suitevscase__order').values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date',
        order=F('suitevscase__order')
    ).annotate(real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj in objects:
        obj['url'] = reverse(case.detail, args=[obj['pk']])
        obj['modified_date_sort'] = obj['modified_date'].strftime('%Y-%m-%d')
        obj['modified_date'] = obj['modified_date'].strftime('%Y-%m-%d %H:%M:%S')
    return JsonResponse({'status': 1, 'message': 'OK', 'data': list(objects)})


# 执行套件
@login_required
def execute_(request, pk):
    try:
        suite_ = Suite.objects.get(pk=pk, is_active=True)
        suite_result = execute_suite(suite_, request.user)
        sub_objects = suite_result.caseresult_set.filter(step_result=None).order_by('case_order')
        suite_result_content = render_to_string('main/include/suite_result_content.html', locals())
        data_dict = dict()
        data_dict['suite_result_content'] = suite_result_content
        data_dict['suite_result_url'] = reverse('result', args=[suite_result.pk])
        return JsonResponse({'status': 1, 'message': 'OK', 'data': data_dict})
    except Suite.DoesNotExist:
        return JsonResponse({'status': 2, 'message': 'Suite does not exist', 'data': None})
