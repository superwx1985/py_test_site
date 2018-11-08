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
from utils.other import get_query_condition, change_to_positive_integer, Cookie, get_project_list
from urllib.parse import quote
from main.views import step, suite, variable_group

logger = logging.getLogger('django.request')


# 用例列表
@login_required
def list_(request):
    if request.session.get('status', None) == 'success':
        prompt = 'success'
    request.session['status'] = None

    project_list = get_project_list()
    has_sub_object = True

    page = request.GET.get('page')
    size = request.GET.get('size', request.COOKIES.get('size'))
    search_text = request.GET.get('search_text', '')
    order_by = request.GET.get('order_by', 'modified_date')
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
    objects2 = Case.objects.filter(is_active=True, step__is_active=True).values('pk').annotate(m2m_count=Count('step'))
    m2m_count = {o['pk']: o['m2m_count'] for o in objects2}

    # 获取被调用次数
    objects2 = Case.objects.filter(is_active=True, suite__is_active=True).values('pk').annotate(
        reference_count=Count('*'))
    count_ = {o['pk']: o['reference_count'] for o in objects2}
    objects3 = Step.objects.filter(
        is_active=True, action__code='OTHER_CALL_SUB_CASE').values('other_sub_case_id').annotate(
        reference_count=Count('*')).order_by()  # 此处加上order_by是因为step默认按修改时间排序，会导致分组加入修改时间
    count_3 = {o['other_sub_case_id']: o['reference_count'] for o in objects3}

    for o in objects:
        # 添加子对象数量
        o['m2m_count'] = m2m_count.get(o['pk'], 0)
        # 添加被调用次数
        o['reference_count'] = count_.get(o['pk'], 0) + count_3.get(o['pk'], 0)

    # 排序
    if objects:
        if order_by not in objects[0]:
            order_by = 'modified_date'
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
    next_ = request.GET.get('next', '/home/')
    inside = request.GET.get('inside')
    new_pk = request.GET.get('new_pk')
    order = request.GET.get('order')
    copy_sub_item = True  # 可以拷贝子对象
    reference_url = reverse(reference, args=[pk])  # 被其他对象调用
    project_list = get_project_list()
    has_sub_object = True
    try:
        obj = Case.objects.select_related('creator', 'modifier').get(pk=pk)
    except Case.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        form = CaseForm(instance=obj)
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        return render(request, 'main/case/detail.html', locals())
    elif request.method == 'POST':
        obj_temp = copy.deepcopy(obj)
        form = CaseForm(data=request.POST, instance=obj_temp)
        try:
            m2m_list = json.loads(request.POST.get('step', 'null'))
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
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            if redirect:
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


@login_required
def add(request):
    next_ = request.GET.get('next', '/home/')
    inside = request.GET.get('inside')
    copy_sub_item = True
    project_list = get_project_list()
    if request.method == 'GET':
        form = CaseForm()
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        return render(request, 'main/case/detail.html', locals())
    elif request.method == 'POST':
        form = CaseForm(data=request.POST)
        try:
            m2m_list = json.loads(request.POST.get('step', 'null'))
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
                        m2m_obj = Step.objects.get(pk=m2m_pk)
                    except Step.DoesNotExist:
                        logger.warning('找不到m2m对象[{}]'.format(m2m_pk), exc_info=True)
                        continue
                    order += 1
                    CaseVsStep.objects.create(case=obj, step=m2m_obj, order=order, creator=request.user,
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

        return render(request, 'main/case/detail.html', locals())


@login_required
def delete(request, pk):
    if request.method == 'POST':
        Case.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


@login_required
def delete(request, pk):
    if request.method == 'POST':
        Case.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


@login_required
def multiple_delete(request):
    if request.method == 'POST':
        try:
            pk_list = json.loads(request.POST['pk_list'])
            Case.objects.filter(pk__in=pk_list, creator=request.user).update(
                is_active=False, modifier=request.user, modified_date=timezone.now())
        except Exception as e:
            return JsonResponse({'statue': 2, 'message': str(e), 'data': None})
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': []})


@login_required
def quick_update(request, pk):
    if request.method == 'POST':
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            obj = Case.objects.get(pk=pk)
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


# 获取选中的step
@login_required
def steps(_, pk):
    objects = Step.objects.filter(case=pk, is_active=True).order_by('casevsstep__order').values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date',
        order=F('casevsstep__order')
    ).annotate(action=Concat('action__type__name', Value(' - '), 'action__name', output_field=CharField()),
               real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj in objects:
        obj['url'] = reverse(step.detail, args=[obj['pk']])
        obj['modified_date_sort'] = obj['modified_date'].strftime('%Y-%m-%d')
        obj['modified_date'] = obj['modified_date'].strftime('%Y-%m-%d %H:%M:%S')
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': list(objects)})


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
    order_by = condition.get('order_by', 'modified_date')
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

    for obj in objects:
        obj['url'] = reverse(detail, args=[obj['pk']])
        obj['modified_date_sort'] = obj['modified_date'].strftime('%Y-%m-%d')
        obj['modified_date'] = obj['modified_date'].strftime('%Y-%m-%d %H:%M:%S')

    return JsonResponse({'statue': 1, 'message': 'OK', 'data': {
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
        objects = Case.objects.filter(pk=pk).values(
            'pk', 'uuid', 'name', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
            real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
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
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': data_list})


# 复制操作
def copy_action(pk, user, copy_sub_item, name_prefix=None):
    obj = Case.objects.get(pk=pk)
    m2m_objects = obj.step.filter(is_active=True).order_by('casevsstep__order')
    obj.pk = None
    if name_prefix:
        obj.name = name_prefix + obj.name
    if copy_sub_item and obj.variable_group:
        obj.variable_group = variable_group.copy_action(obj.variable_group.pk, user, name_prefix)
    obj.creator = obj.modifier = user
    obj.uuid = uuid.uuid1()
    obj.clean_fields()
    obj.save()
    m2m_order = 0
    for m2m_obj in m2m_objects:
        if copy_sub_item:
            m2m_obj = step.copy_action(m2m_obj.pk, user, name_prefix)
            # m2m_obj.pk = None
            # m2m_obj.creator = m2m_obj.modifier = user
            # m2m_obj.uuid = uuid.uuid1()
            # m2m_obj.clean_fields()
            # m2m_obj.save()
        m2m_order += 1
        CaseVsStep.objects.create(
            case=obj, step=m2m_obj, order=m2m_order, creator=user, modifier=user)
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
            'statue': 1, 'message': 'OK', 'data': {
                'new_pk': obj.pk, 'new_url': reverse(detail, args=[obj.pk]), 'order': order}
        })
    except Exception as e:
        return JsonResponse({'statue': 2, 'message': str(e), 'data': None})


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
            return JsonResponse({'statue': 2, 'message': str(e), 'data': None})
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': []})


# 获取带搜索信息的下拉列表数据
@login_required
def select_json(request):
    condition = request.POST.get('condition', '{}')
    try:
        condition = json.loads(condition)
    except json.decoder.JSONDecodeError:
        condition = dict()
    selected_pk = condition.get('selected_pk')
    objects = Case.objects.filter(is_active=True).values('pk', 'uuid', 'name', 'keyword', 'project__name')

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
        d['url'] = '{}?next={}'.format(reverse(detail, args=[obj['pk']]), reverse(list_))
        data.append(d)

    return JsonResponse({'statue': 1, 'message': 'OK', 'data': data})


# 获取调用列表
def reference(request, pk):
    try:
        obj = Case.objects.get(pk=pk)
    except Case.DoesNotExist:
        raise Http404('Case does not exist')
    objects = obj.suite_set.filter(is_active=True).order_by('-modified_date').values(
        'pk', 'uuid', 'name', 'keyword', 'creator', 'creator__username', 'modified_date', 'suitevscase__order').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj_ in objects:
        obj_['url'] = '{}?next={}'.format(reverse(suite.detail, args=[obj_['pk']]), reverse(suite.list_))
        obj_['type'] = '套件'
        obj_['order'] = obj_['suitevscase__order']
    action = Action.objects.get(code='OTHER_CALL_SUB_CASE')
    objects2 = Step.objects.filter(is_active=True, other_sub_case=obj, action=action).order_by('-modified_date').values(
        'pk', 'uuid', 'name', 'keyword', 'creator', 'creator__username', 'modified_date').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj_ in objects2:
        obj_['url'] = '{}?next={}'.format(reverse(step.detail, args=[obj_['pk']]), reverse(step.list_))
        obj_['type'] = '步骤'
    objects = list(objects)
    objects.extend(list(objects2))

    return render(request, 'main/include/detail_reference.html', locals())
