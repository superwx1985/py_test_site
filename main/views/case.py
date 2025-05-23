import json
import logging
import copy
import uuid
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import Q, F, CharField, Value, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import Case, Step, CaseVsStep, Action
from main.forms import OrderByForm, PaginatorForm, CaseForm
from main.views.general import sort_list, generate_new_name
from utils.other import get_query_condition, change_to_positive_integer, Cookie, get_project_list, check_admin,\
    check_recursive_call
from urllib.parse import quote
from main.views import step, suite, variable_group, config, data_set
from utils import system

logger = logging.getLogger('django.request')


# 用例列表
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

    objects = Case.objects.filter(q).values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    m2m_objects = Case.objects.filter(
        is_active=True, step__is_active=True).values('pk').annotate(m2m_count=Count('step'))
    m2m_count = {o['pk']: o['m2m_count'] for o in m2m_objects}

    # 获取被调用次数
    reference_objects1 = Case.objects.filter(is_active=True, suite__is_active=True).values('pk').annotate(
        reference_count=Count('*'))
    reference_count1 = {o['pk']: o['reference_count'] for o in reference_objects1}
    reference_objects2 = Step.objects.filter(
        is_active=True, action__code='OTHER_CALL_SUB_CASE').values('other_sub_case_id').annotate(
        reference_count=Count('*')).order_by()  # 此处加上order_by是因为step默认按修改时间排序，会导致分组加入修改时间
    reference_count2 = {o['other_sub_case_id']: o['reference_count'] for o in reference_objects2}

    for o in objects:
        # 添加子对象数量
        o['m2m_count'] = m2m_count.get(o['pk'], 0)
        # 添加被调用次数
        o['reference_count'] = reference_count1.get(o['pk'], 0) + reference_count2.get(o['pk'], 0)

    # 排序
    if objects and order_by not in objects[0]:
        order_by = 'pk'
    objects = sorted(objects, key=lambda x: x[order_by], reverse=order_by_reverse)
    # 分页
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
    respond = render(request, 'main/case/list.html', locals())
    for cookie in cookies:
        respond.set_cookie(cookie.key, cookie.value, cookie.max_age, cookie.expires, cookie.path)
    return respond


# 用例详情
@login_required
def detail(request, pk):
    next_ = request.GET.get('next', '')
    inside = request.GET.get('inside')
    new_pk = request.GET.get('new_pk')
    order = request.GET.get('order')
    copy_sub_item = True  # 可以拷贝子对象
    reference_url = reverse(reference, args=[pk])  # 被其他对象调用
    project_list = get_project_list()
    has_sub_object = True
    is_admin = check_admin(request.user)

    try:
        obj = Case.objects.select_related('creator', 'modifier').get(pk=pk)
    except Case.DoesNotExist:
        raise Http404('Case does not exist')

    if request.method == 'POST' and (is_admin or request.user == obj.creator):
        obj_temp = copy.deepcopy(obj)
        form = CaseForm(data=request.POST, instance=obj_temp)
        try:
            m2m_list = json.loads(request.POST.get('step', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            m2m_list = None
        if form.is_valid():
            obj_temp = form.save(commit=False)
            obj_temp.modifier = request.user
            obj_temp.save()
            if m2m_list is not None:
                m2m = CaseVsStep.objects.filter(case=obj).order_by('order')
                original_m2m_list = list()
                for dict_ in m2m.values('step'):
                    original_m2m_list.append(str(dict_['step']))
                if original_m2m_list != m2m_list:
                    m2m.delete()
                    order = 0
                    for m2m_pk in m2m_list:
                        if m2m_pk is None or m2m_pk.strip() == '':
                            continue
                        try:
                            m2m_obj = Step.objects.get(pk=m2m_pk)
                        except Step.DoesNotExist:
                            logger.warning('找不到m2m对象[{}]'.format(m2m_pk), exc_info=True)
                            continue
                        order += 1
                        CaseVsStep.objects.create(case=obj, step=m2m_obj, order=order, creator=request.user,
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
            if m2m_list is not None:
                # 暂存step列表
                m2m = CaseVsStep.objects.filter(case=obj).order_by('order')
                original_m2m_list = list()
                for dict_ in m2m.values('step'):
                    original_m2m_list.append(str(dict_['step']))
                temp_list = list()
                temp_dict = dict()
                if original_m2m_list != m2m_list:
                    temp_list_json = json.dumps(m2m_list)

        return render(request, 'main/case/detail.html', locals())
    else:
        form = CaseForm(instance=obj)
        if request.session.get('state', None) == 'success':
            prompt = 'success'
        request.session['state'] = None
        return render(request, 'main/case/detail.html', locals())


@login_required
def add(request):
    next_ = request.GET.get('next', '')
    inside = request.GET.get('inside')
    copy_sub_item = True
    project_list = get_project_list()

    parent_project = request.GET.get('parent_project')

    if request.method == 'POST':
        form = CaseForm(data=request.POST)
        try:
            m2m_list = json.loads(request.POST.get('step', 'null'))
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
                        m2m_obj = Step.objects.get(pk=m2m_pk)
                    except Step.DoesNotExist:
                        logger.warning('找不到m2m对象[{}]'.format(m2m_pk), exc_info=True)
                        continue
                    order += 1
                    CaseVsStep.objects.create(case=obj, step=m2m_obj, order=order, creator=request.user,
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
            if m2m_list is not None:
                temp_list_json = json.dumps(m2m_list)

        return render(request, 'main/case/detail.html', locals())
    else:
        if parent_project:
            form = CaseForm(initial={'project': parent_project})
        else:
            form = CaseForm()
        if request.session.get('state', None) == 'success':
            prompt = 'success'
        request.session['state'] = None
        return render(request, 'main/case/detail.html', locals())


@login_required
def delete(request, pk):
    err = None
    if request.method == 'POST':
        try:
            obj = Case.objects.select_related('creator', 'modifier').get(pk=pk)
            # obj = Case.objects.get(pk=pk)
        except Case.DoesNotExist:
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
                Case.objects.filter(pk__in=pk_list).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
            else:
                Case.objects.filter(pk__in=pk_list, creator=request.user).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
        except Exception as e:
            return JsonResponse({'state': 2, 'message': str(e), 'data': None})
        return JsonResponse({'state': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'state': 2, 'message': 'Only accept "POST" method', 'data': []})


@login_required
def multiple_delete(request):
    if request.method == 'POST':
        try:
            pk_list = json.loads(request.POST['pk_list'])
            is_admin = check_admin(request.user)
            if is_admin:
                Case.objects.filter(pk__in=pk_list).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
            else:
                Case.objects.filter(pk__in=pk_list, creator=request.user).update(
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
            obj = Case.objects.get(pk=pk)
            if col_name in ('name', 'keyword'):
                is_admin = check_admin(request.user)
                if is_admin or obj.creator == request.user:
                    setattr(obj, col_name, new_value)
                    obj.clean_fields()
                    obj.modifier = request.user
                    obj.save()
                else:
                    raise PermissionError('无权限')
            else:
                raise ValueError('非法的字段名称')
        except Exception as e:
            return JsonResponse({'state': 2, 'message': str(e), 'data': None})
        return JsonResponse({'state': 1, 'message': 'OK', 'data': new_value})
    else:
        return JsonResponse({'state': 2, 'message': 'Only accept "POST" method', 'data': None})


# 获取选中的step
@login_required
def steps(_, pk):
    objects = Step.objects.filter(case=pk, is_active=True).order_by('casevsstep__order').values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date',
        order=F('casevsstep__order')
    ).annotate(action=Concat('action__type__name', Value('-'), 'action__name', output_field=CharField()),
               real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj in objects:
        obj['url'] = reverse(step.detail, args=[obj['pk']])
        obj['modified_date_sort'] = obj['modified_date'].strftime('%Y-%m-%d')
        obj['modified_date'] = obj['modified_date'].strftime('%Y-%m-%d %H:%M:%S')
    return JsonResponse({'state': 1, 'message': 'OK', 'data': list(objects)})


# 获取m2m json
@login_required
def list_json(request):
    condition = request.POST.get('condition', '{}')
    try:
        condition = json.loads(condition)
    except json.decoder.JSONDecodeError:
        condition = dict()

    page = condition.get('page')
    size = 10
    search_text = condition.get('search_text', '')
    order_by = condition.get('order_by', 'pk')
    order_by_reverse = condition.get('order_by_reverse', 'True')
    all_ = condition.get('all_', 'False')
    search_project = condition.get('search_project', None)

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

    objects = Case.objects.filter(q).values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))

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

    for obj in objects:
        obj['url'] = reverse(detail, args=[obj['pk']])
        obj['modified_date_sort'] = obj['modified_date'].strftime('%Y-%m-%d')
        obj['modified_date'] = obj['modified_date'].strftime('%Y-%m-%d %H:%M:%S')

    return JsonResponse({'state': 1, 'message': 'OK', 'data': {
        'objects': list(objects), 'page': page, 'max_page': paginator.num_pages, 'size': size}})


# 获取临时m2m
@login_required
def list_temp(request):
    pk_list = json.loads(request.POST.get('condition', ''))
    order = 0
    data_list = list()
    for pk in pk_list:
        if pk.strip() == '':
            continue
        try:
            objects = Case.objects.filter(pk=pk).values(
                'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date'
            ).annotate(
                real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField())
            )
        except ValueError as e:
            logger.error(e)
            continue
        if not objects:
            continue
        objects = list(objects)
        order += 1
        obj = objects[0]
        obj['order'] = order
        obj['url'] = reverse(detail, args=[pk])
        obj['modified_date_sort'] = obj['modified_date'].strftime('%Y-%m-%d')
        obj['modified_date'] = obj['modified_date'].strftime('%Y-%m-%d %H:%M:%S')
        data_list.append(objects[0])
    return JsonResponse({'state': 1, 'message': 'OK', 'data': data_list})


# 复制操作
def copy_action(pk, user, new_name=None, name_prefix=None, copy_sub_item=None, copied_items=None):
    if not copied_items:
        copied_items = [dict()]
    obj = Case.objects.get(pk=pk)
    original_obj_uuid = obj.uuid
    if original_obj_uuid in copied_items[0]:  # 判断是否已被复制
        return copied_items[0][original_obj_uuid]

    if copy_sub_item:
        recursive_id, case_list = check_recursive_call(obj)
        if recursive_id:
            raise RecursionError('用例[ID:{}]被用例[ID:{}]递归调用，复制中止。调用顺序列表：{}'.format(
                recursive_id, case_list[-1], case_list))
    m2m_objects = obj.step.filter(is_active=True).order_by('casevsstep__order') or []

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
        if obj.data_set:
            obj.data_set = data_set.copy_action(obj.data_set.pk, user, None, name_prefix, copied_items)

    obj.creator = obj.modifier = user
    obj.uuid = uuid.uuid1()
    obj.clean_fields()
    obj.save()

    m2m_order = 0
    for m2m_obj in m2m_objects:
        # 判断是否需要复制子对象
        if copy_sub_item:
            # # 判断是否已被复制
            # if m2m_obj in copied_items[0]:
            #     m2m_obj_ = copied_items[0][m2m_obj]
            # else:
            #     m2m_obj_ = step.copy_action(m2m_obj.pk, user, name_prefix, copy_sub_item, copied_items)
            #     copied_items[0][m2m_obj] = m2m_obj_
            m2m_obj_ = step.copy_action(m2m_obj.pk, user, None, name_prefix, copy_sub_item, copied_items)
        else:
            m2m_obj_ = m2m_obj
        m2m_order += 1
        CaseVsStep.objects.create(case=obj, step=m2m_obj_, order=m2m_order, creator=user, modifier=user)

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
    objects = Case.objects.filter(is_active=True).values('pk', 'uuid', 'name', 'keyword', 'project__name')

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


# 获取调用列表
def reference(request, pk):
    try:
        obj = Case.objects.get(pk=pk)
    except Case.DoesNotExist:
        raise Http404('Case does not exist')
    objects = obj.suite_set.filter(is_active=True).order_by('-modified_date').values(
        'pk', 'uuid', 'name', 'keyword', 'creator', 'creator__username', 'modified_date',
        'suitevscase__order').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj_ in objects:
        # obj_['url'] = '{}?next={}'.format(reverse(suite.detail, args=[obj_['pk']]), reverse(suite.list_))
        obj_['url'] = reverse(suite.detail, args=[obj_['pk']])
        obj_['type'] = '套件'
        obj_['order'] = obj_['suitevscase__order']
    action = Action.objects.get(code='OTHER_CALL_SUB_CASE')
    objects2 = Step.objects.filter(is_active=True, other_sub_case=obj, action=action).order_by('-modified_date').values(
        'pk', 'uuid', 'name', 'keyword', 'creator', 'creator__username', 'modified_date').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj_ in objects2:
        # obj_['url'] = '{}?next={}'.format(reverse(step.detail, args=[obj_['pk']]), reverse(step.list_))
        obj_['url'] = reverse(step.detail, args=[obj_['pk']])
        obj_['type'] = '步骤'
    objects = list(objects)
    objects.extend(list(objects2))

    return render(request, 'main/include/detail_reference.html', locals())


# 查看状态
@login_required
def status(request, execute_uuid):
    is_admin = check_admin(request.user)
    running_suite = system.RUNNING_SUITES.get_suite(execute_uuid)
    return render(request, 'main/case/status.html', locals())


# 中止
@login_required
def stop(request):
    execute_uuid = request.POST.get('execute_uuid')
    case_order = request.POST.get('case_order')

    success = False

    if execute_uuid and case_order:
        if check_admin(request.user):
            user = None
        else:
            user = request.user
        try:
            case_order = int(case_order)
        except (ValueError, TypeError):
            msg = '无效的用例编号'
        else:
            success, msg = system.RUNNING_SUITES.stop_case(execute_uuid, case_order, user)
    else:
        msg = '未提供执行ID或用例编号'

    if success:
        return JsonResponse({'state': 1, 'message': msg, 'data': execute_uuid})
    else:
        return JsonResponse({'state': 2, 'message': msg, 'data': execute_uuid})


# 暂停
@login_required
def pause(request):
    execute_uuid = request.POST.get('execute_uuid')
    case_order = request.POST.get('case_order')

    success = False

    if execute_uuid and case_order:
        if check_admin(request.user):
            user = None
        else:
            user = request.user
        try:
            case_order = int(case_order)
        except (ValueError, TypeError):
            msg = '无效的用例编号'
        else:
            success, msg = system.RUNNING_SUITES.pause_case(execute_uuid, case_order, user)
    else:
        msg = '未提供执行ID或用例编号'

    if success:
        return JsonResponse({'state': 1, 'message': msg, 'data': execute_uuid})
    else:
        return JsonResponse({'state': 2, 'message': msg, 'data': execute_uuid})


# 继续
@login_required
def continue_(request):
    execute_uuid = request.POST.get('execute_uuid')
    case_order = request.POST.get('case_order')

    success = False

    if execute_uuid and case_order:
        if check_admin(request.user):
            user = None
        else:
            user = request.user
        try:
            case_order = int(case_order)
        except (ValueError, TypeError):
            msg = '无效的用例编号'
        else:
            success, msg = system.RUNNING_SUITES.continue_case(execute_uuid, case_order, user)
    else:
        msg = '未提供执行ID或用例编号'

    if success:
        return JsonResponse({'state': 1, 'message': msg, 'data': execute_uuid})
    else:
        return JsonResponse({'state': 2, 'message': msg, 'data': execute_uuid})