import json
import logging
import copy
import uuid
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import Q, Count, CharField
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import VariableGroup, Variable, Case, Suite
from main.forms import OrderByForm, PaginatorForm, VariableGroupForm
from main.views.general import sort_list, generate_new_name
from utils.other import get_query_condition, change_to_positive_integer, Cookie, get_project_list, check_admin
from urllib.parse import quote
from main.views import case, suite

logger = logging.getLogger('django.request')


@login_required
def list_(request):
    if request.session.get('state', None) == 'success':
        prompt = 'success'
    request.session['state'] = None

    project_list = get_project_list()
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

    objects = VariableGroup.objects.filter(q).values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
        variable_count=Count('variable'),
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))

    # 获取被调用次数
    reference_objects1 = VariableGroup.objects.filter(is_active=True, case__is_active=True).values('pk').annotate(
        reference_count=Count('*'))
    reference_count1 = {o['pk']: o['reference_count'] for o in reference_objects1}
    reference_objects2 = VariableGroup.objects.filter(is_active=True, suite__is_active=True).values('pk').annotate(
        reference_count=Count('*'))
    reference_count2 = {o['pk']: o['reference_count'] for o in reference_objects2}
    for o in objects:
        o['reference_count'] = reference_count1.get(o['pk'], 0) + reference_count2.get(o['pk'], 0)

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
    respond = render(request, 'main/variable_group/list.html', locals())
    for cookie in cookies:
        respond.set_cookie(cookie.key, cookie.value, cookie.max_age, cookie.expires, cookie.path)
    return respond


@login_required
def detail(request, pk):
    next_ = request.GET.get('next', '')
    inside = request.GET.get('inside')
    new_pk = request.GET.get('new_pk')
    reference_url = reverse(reference, args=[pk])  # 被其他对象调用
    is_admin = check_admin(request.user)

    try:
        obj = VariableGroup.objects.select_related('creator', 'modifier').get(pk=pk)
    except VariableGroup.DoesNotExist:
        raise Http404('Variable Group does not exist')

    if request.method == 'POST' and (is_admin or request.user == obj.creator):
        obj_temp = copy.deepcopy(obj)
        form = VariableGroupForm(data=request.POST, instance=obj_temp)
        try:
            variable_list = json.loads(request.POST.get('variable', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            variable_list = None
        if form.is_valid():
            obj_temp = form.save(commit=False)
            obj_temp.modifier = request.user
            obj_temp.save()
            form.save_m2m()
            if variable_list is not None:
                objects = Variable.objects.filter(variable_group=obj)
                object_values = objects.order_by('order').values('name', 'value', 'description')
                object_values = list(object_values)
                if object_values != variable_list:
                    objects.delete()
                    order = 0
                    for v in variable_list:
                        _name = str(v['name']).strip()
                        if not v or v['name'] is None or _name == '':
                            continue
                        else:
                            order += 1
                            try:
                                Variable.objects.create(
                                    variable_group=obj, name=_name, value=v['value'],
                                    description=v['description'], order=order)
                            except Exception as e:
                                form.add_error(None, '添加子对象[{}]时出错：{}'.format(_name, str(e)))
            if not form.non_field_errors():
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

        if variable_list is not None:
            # 暂存variable列表
            temp_dict = dict()
            temp_dict['data'] = variable_list
            temp_list_json = json.dumps(temp_dict)

        return render(request, 'main/variable_group/detail.html', locals())
    else:
        form = VariableGroupForm(instance=obj)
        if request.session.get('state', None) == 'success':
            prompt = 'success'
        request.session['state'] = None
        return render(request, 'main/variable_group/detail.html', locals())


@login_required
def add(request):
    next_ = request.GET.get('next', '')
    inside = request.GET.get('inside')

    if request.method == 'POST':
        form = VariableGroupForm(data=request.POST)
        try:
            variable_list = json.loads(request.POST.get('variable', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            variable_list = None
        if form.is_valid():
            obj_temp = form.save(commit=False)
            obj_temp.creator = obj_temp.modifier = request.user
            obj_temp.save()
            form.save_m2m()
            obj = obj_temp
            pk = obj.id
            if variable_list:
                order = 0
                for v in variable_list:
                    if not v:
                        continue
                    order += 1
                    _name = str(v['name']).strip()
                    if not v or v['name'] is None or _name == '':
                        continue
                    else:
                        try:
                            Variable.objects.create(
                                variable_group=obj, name=_name, value=v['value'], description=v['description'],
                                order=order)
                        except Exception as e:
                            form.add_error(None, '添加子对象[{}]时出错：{}'.format(_name, str(e)))
            if not form.non_field_errors():
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

        if variable_list:
            # 暂存variable列表
            temp_dict = dict()
            temp_dict['data'] = variable_list
            temp_list_json = json.dumps(temp_dict)

        return render(request, 'main/variable_group/detail.html', locals())
    else:
        form = VariableGroupForm()
        if request.session.get('state', None) == 'success':
            prompt = 'success'
        request.session['state'] = None
        return render(request, 'main/variable_group/detail.html', locals())


@login_required
def delete(request, pk):
    err = None
    if request.method == 'POST':
        try:
            obj = VariableGroup.objects.select_related('creator', 'modifier').get(pk=pk)
        except VariableGroup.DoesNotExist:
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
                VariableGroup.objects.filter(pk__in=pk_list).update(
                    is_active=False, modifier=request.user, modified_date=timezone.now())
            else:
                VariableGroup.objects.filter(pk__in=pk_list, creator=request.user).update(
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
            obj = VariableGroup.objects.get(pk=pk)
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


# 获取变量组中的变量
@login_required
def variables(_, pk):
    objects = Variable.objects.filter(variable_group=pk).order_by('order').values(
        'pk', 'uuid', 'name', 'value', 'description')
    return JsonResponse({'state': 1, 'message': 'OK', 'data': list(objects)})


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
    # objects = VariableGroup.objects.filter(is_active=True).values('pk').annotate(name_=Concat(
    #     'pk', Value(' | '), 'name', Value(' | '), 'keyword', Value(' | '), 'project__name', output_field=CharField()),
    # )
    objects = VariableGroup.objects.filter(is_active=True).values('pk', 'uuid', 'name', 'keyword', 'project__name')

    data = []
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

    return JsonResponse({'state': 1, 'message': 'OK', 'data': data})


# 复制操作
def copy_action(pk, user, new_name=None, name_prefix=None, copied_items=None):
    if not copied_items:
        copied_items = [{}]
    obj = VariableGroup.objects.get(pk=pk)
    original_obj_uuid = obj.uuid
    if original_obj_uuid in copied_items[0]:  # 判断是否已被复制
        return copied_items[0][original_obj_uuid]
    sub_object_values = list(
        Variable.objects.filter(variable_group=obj).order_by('order').values('name', 'value', 'description'))

    obj.pk = None
    obj.name = generate_new_name(obj.name, new_name, name_prefix)
    obj.creator = obj.modifier = user
    obj.uuid = uuid.uuid1()
    obj.clean_fields()
    obj.save()

    order = 0
    for v in sub_object_values:
        if not v or v['name'] is None or v['name'].strip() == '':
            continue
        else:
            order += 1
            Variable.objects.create(
                variable_group=obj, name=v['name'].strip(), value=v['value'], description=v['description'], order=order)

    copied_items[0][original_obj_uuid] = obj
    return obj


# 复制
@login_required
def copy_(request, pk):
    new_name = request.POST.get('new_name')
    name_prefix = request.POST.get('name_prefix')
    try:
        obj = copy_action(pk, request.user, new_name, name_prefix)
        return JsonResponse({
            'state': 1, 'message': 'OK', 'data': {
                'new_pk': obj.pk, 'new_url': reverse(detail, args=[obj.pk])}
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
            copied_items = [dict()]
            new_pk_list = list()
            for pk in pk_list:
                new_obj = copy_action(pk, request.user, None, name_prefix, copied_items)
                new_pk_list.append(new_obj.pk)
        except Exception as e:
            return JsonResponse({'state': 2, 'message': str(e), 'data': None})
        return JsonResponse({'state': 1, 'message': 'OK', 'data': new_pk_list})
    else:
        return JsonResponse({'state': 2, 'message': 'Only accept "POST" method', 'data': []})


# 获取调用列表
def reference(request, pk):
    try:
        obj = VariableGroup.objects.get(pk=pk)
    except VariableGroup.DoesNotExist:
        raise Http404('Variable Group does not exist')
    objects = Case.objects.filter(is_active=True, variable_group=obj).order_by('-modified_date').values(
        'pk', 'uuid', 'name', 'keyword', 'creator', 'creator__username', 'modified_date').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj_ in objects:
        obj_['url'] = reverse(case.detail, args=[obj_['pk']])
        obj_['type'] = '用例'
    objects2 = Suite.objects.filter(is_active=True, variable_group=obj).order_by('-modified_date').values(
        'pk', 'uuid', 'name', 'keyword', 'creator', 'creator__username', 'modified_date').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj_ in objects2:
        obj_['url'] = reverse(suite.detail, args=[obj_['pk']])
        obj_['type'] = '套件'
    objects = list(objects)
    objects.extend(list(objects2))

    return render(request, 'main/include/detail_reference.html', locals())
