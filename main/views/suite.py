import json
import logging
import copy
import uuid
import threading
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
from main.views.general import sort_list, generate_new_name
from utils.other import get_query_condition, change_to_positive_integer, Cookie, get_project_list, check_admin
from urllib.parse import quote
from main.views import case, config, variable_group, element_group
from utils import system, thread_pool
from django.conf import settings

logger = logging.getLogger('django.request')


# 列表
@login_required
def list_(request):
    if request.session.get('state', None) == 'success':
        prompt = 'success'
    request.session['state'] = None

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

    if objects:
        objects = sort_list(objects, order_by, order_by_reverse)

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
    next_ = request.GET.get('next', '')
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
            request.session['state'] = 'success'
            _redirect = request.POST.get('redirect')
            if _redirect:
                if _redirect == 'close':
                    request.session['state'] = None
                    return render(request, 'main/other/close.html')
                if not next_:
                    next_ = reverse(list_)
                    request.session['state'] = None
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect(request.get_full_path())
        else:
            temp_config = request.POST.get('config')
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
        if request.session.get('state', None) == 'success':
            prompt = 'success'
        request.session['state'] = None
        return render(request, 'main/suite/detail.html', locals())


@login_required
def add(request):
    next_ = request.GET.get('next', '')
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
            request.session['state'] = 'success'
            _redirect = request.POST.get('redirect')
            if _redirect == 'add_another':
                return HttpResponseRedirect(request.get_full_path())
            elif _redirect:
                if _redirect == 'close':
                    request.session['state'] = None
                    return render(request, 'main/other/close.html')
                if not next_:
                    next_ = reverse(list_)
                    request.session['state'] = None
                return HttpResponseRedirect(next_)
            else:
                para = ''
                if inside:  # 如果是内嵌网页，则加上内嵌标志后再跳转
                    para = '&inside=1&new_pk={}'.format(pk)
                return HttpResponseRedirect('{}?next={}{}'.format(reverse(detail, args=[pk]), quote(next_), para))
        else:
            temp_config = request.POST.get('config')
            temp_variable_group = request.POST.get('variable_group')
            temp_config = request.POST.get('config')
            if m2m_list is not None:
                temp_list_json = json.dumps(m2m_list)

        return render(request, 'main/suite/detail.html', locals())
    else:
        form = SuiteForm()
        if request.session.get('state', None) == 'success':
            prompt = 'success'
        request.session['state'] = None
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
        return JsonResponse({'state': 2, 'message': err, 'data': pk})
    else:
        return JsonResponse({'state': 1, 'message': 'OK', 'data': pk})


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
            return JsonResponse({'state': 2, 'message': str(e), 'data': None})
        return JsonResponse({'state': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'state': 2, 'message': 'Only accept "POST" method', 'data': []})


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
            return JsonResponse({'state': 2, 'message': str(e), 'data': None})
        return JsonResponse({'state': 1, 'message': 'OK', 'data': new_value})
    else:
        return JsonResponse({'state': 2, 'message': 'Only accept "POST" method', 'data': None})


# 获取带搜索信息的下拉列表数据
@login_required
def select_json(request):
    condition = request.POST.get('condition', '{}')
    try:
        condition = json.loads(condition)
    except json.decoder.JSONDecodeError:
        condition = {}
    selected_pk = condition.get('selected_pk')
    url_format = condition.get('url_format')
    url_replacer = condition.get('url_replacer')
    objects = Suite.objects.filter(is_active=True).values('pk', 'name', 'keyword', 'project__name')

    data = []
    for obj in objects:
        d = {}
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

    return JsonResponse({'state': 1, 'message': 'OK', 'data': data})


# 复制操作
def copy_action(pk, user, new_name=None, name_prefix=None, copy_sub_item=None, copied_items=None):
    if not copied_items:
        copied_items = [{}]
    obj = Suite.objects.get(pk=pk)
    original_obj_uuid = obj.uuid
    if original_obj_uuid in copied_items[0]:  # 判断是否已被复制
        return copied_items[0][original_obj_uuid]
    m2m_objects = obj.case.filter(is_active=True).order_by('suitevscase__order') or []
    obj.pk = None
    obj.name = generate_new_name(obj.name, new_name, name_prefix)

    if copy_sub_item:
        if obj.config:
            # if obj.config in copied_items[0]:  # 判断是否已被复制
            #     obj.config = copied_items[0][obj.config]
            # else:
            #     new_sub_obj = config.copy_action(obj.config.pk, user, name_prefix)
            #     copied_items[0][obj.config] = obj.config = new_sub_obj
            obj.config = config.copy_action(obj.config.pk, user, None, name_prefix, copied_items)
        if obj.variable_group:
            # if obj.variable_group in copied_items[0]:  # 判断是否已被复制
            #     obj.variable_group = copied_items[0][obj.variable_group]
            # else:
            #     new_sub_obj = variable_group.copy_action(obj.variable_group.pk, user, name_prefix)
            #     copied_items[0][obj.variable_group] = obj.variable_group = new_sub_obj
            obj.variable_group = variable_group.copy_action(obj.variable_group.pk, user, None, name_prefix, copied_items)
        if obj.element_group:
            # if obj.element_group in copied_items[0]:  # 判断是否已被复制
            #     obj.element_group = copied_items[0][obj.element_group]
            # else:
            #     new_sub_obj = element_group.copy_action(obj.element_group.pk, user, name_prefix)
            #     copied_items[0][obj.element_group] = obj.element_group = new_sub_obj
            obj.element_group = element_group.copy_action(obj.element_group.pk, user, None, name_prefix, copied_items)

    obj.creator = obj.modifier = user
    obj.uuid = uuid.uuid1()
    obj.clean_fields()
    obj.save()

    m2m_order = 0
    for m2m_obj in m2m_objects:
        # 判断是否需要复制子对象
        if copy_sub_item:
            # # 判断子对象是否已被复制
            # if m2m_obj in copied_items[0]:
            #     m2m_obj_ = copied_items[0][m2m_obj]
            # else:
            #     m2m_obj_ = case.copy_action(m2m_obj.pk, user, name_prefix, copy_sub_item, copied_items)
            #     copied_items[0][m2m_obj] = m2m_obj_
            m2m_obj_ = case.copy_action(m2m_obj.pk, user, None, name_prefix, copy_sub_item, copied_items)
        else:
            m2m_obj_ = m2m_obj
        m2m_order += 1
        SuiteVsCase.objects.create(
            suite=obj, case=m2m_obj_, order=m2m_order, creator=user, modifier=user)

    copied_items[0][original_obj_uuid] = obj
    return obj


# 复制
@login_required
def copy_(request, pk):
    new_name = request.POST.get('new_name')
    name_prefix = request.POST.get('name_prefix')
    order = request.POST.get('order')
    order = change_to_positive_integer(order, 0)
    copy_sub_item = request.POST.get('copy_sub_item')
    try:
        obj = copy_action(pk, request.user, new_name, name_prefix, copy_sub_item)
        return JsonResponse({
            'state': 1, 'message': 'OK', 'data': {
                'new_pk': obj.pk, 'new_url': reverse(detail, args=[obj.pk]), 'order': order}
        })
    except Exception as e:
        return JsonResponse({'state': 2, 'message': str(e), 'data': None})


# 批量复制
@login_required
def multiple_copy(request):
    if request.method == 'POST':
        try:
            pk_list = json.loads(request.POST['pk_list'])
            name_prefix = request.POST.get('name_prefix', '')
            copied_items = [{}]
            new_pk_list = []
            for pk in pk_list:
                new_obj = copy_action(pk, request.user, None, name_prefix, None, copied_items)
                new_pk_list.append(new_obj.pk)
        except Exception as e:
            return JsonResponse({'state': 2, 'message': str(e), 'data': None})
        return JsonResponse({'state': 1, 'message': 'OK', 'data': new_pk_list})
    else:
        return JsonResponse({'state': 2, 'message': 'Only accept "POST" method', 'data': []})


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
    return JsonResponse({'state': 1, 'message': 'OK', 'data': list(objects)})


# 查看状态
@login_required
def status(request):
    is_admin = check_admin(request.user)
    suites = system.RUNNING_SUITES.get_suites()
    active_thread = threading.active_count()
    pool_size = settings.SUITE_MAX_CONCURRENT_EXECUTE_COUNT
    pool_state = '使用中' if thread_pool.SUITE_EXECUTE_POOL else '已关闭'
    return render(request, 'main/suite/status.html', locals())


# 中止
@login_required
def stop(request):
    execute_uuid = request.POST.get('execute_uuid')

    if execute_uuid:
        if check_admin(request.user):
            user = None
        else:
            user = request.user
        success, msg = system.RUNNING_SUITES.stop_suite(execute_uuid, user)
    else:
        success = False
        msg = '未提供执行ID'

    if success:
        return JsonResponse({'state': 1, 'message': msg, 'data': execute_uuid})
    else:
        return JsonResponse({'state': 2, 'message': msg, 'data': execute_uuid})


# 暂停
@login_required
def pause(request):
    execute_uuid = request.POST.get('execute_uuid')

    if execute_uuid:
        if check_admin(request.user):
            user = None
        else:
            user = request.user
        success, msg = system.RUNNING_SUITES.pause_suite(execute_uuid, user)
    else:
        success = False
        msg = '未提供执行ID'

    if success:
        return JsonResponse({'state': 1, 'message': msg, 'data': execute_uuid})
    else:
        return JsonResponse({'state': 2, 'message': msg, 'data': execute_uuid})


# 继续
@login_required
def continue_(request):
    execute_uuid = request.POST.get('execute_uuid')

    if execute_uuid:
        if check_admin(request.user):
            user = None
        else:
            user = request.user
        success, msg = system.RUNNING_SUITES.continue_suite(execute_uuid, user)
    else:
        success = False
        msg = '未提供执行ID'

    if success:
        return JsonResponse({'state': 1, 'message': msg, 'data': execute_uuid})
    else:
        return JsonResponse({'state': 2, 'message': msg, 'data': execute_uuid})