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
from main.models import ElementGroup, Element, Step, Suite
from main.forms import OrderByForm, PaginatorForm, ElementGroupForm
from utils.other import get_query_condition, change_to_positive_integer, Cookie, get_project_list
from urllib.parse import quote
from main.views import suite

logger = logging.getLogger('django.request')


@login_required
def list_(request):
    if request.session.get('status', None) == 'success':
        prompt = 'success'
    request.session['status'] = None

    project_list = get_project_list()

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

    objects = ElementGroup.objects.filter(q).values(
        'pk', 'uuid', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
        element_count=Count('element'),
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))

    # 获取被调用次数
    objects2 = ElementGroup.objects.filter(is_active=True, suite__is_active=True).values('pk').annotate(
        reference_count=Count('*'))
    count_ = {o['pk']: o['reference_count'] for o in objects2}

    for o in objects:
        o['reference_count'] = count_.get(o['pk'], 0)

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
    respond = render(request, 'main/element_group/list.html', locals())
    for cookie in cookies:
        respond.set_cookie(cookie.key, cookie.value, cookie.max_age, cookie.expires, cookie.path)
    return respond


@login_required
def detail(request, pk):
    next_ = request.GET.get('next', '/home/')
    reference_url = reverse(reference, args=[pk])  # 被其他对象调用
    by_list_json = json.dumps(Step.ui_by_list)
    try:
        obj = ElementGroup.objects.select_related('creator', 'modifier').get(pk=pk)
    except ElementGroup.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        form = ElementGroupForm(instance=obj)
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/element_group/detail.html', locals())
    elif request.method == 'POST':
        obj_temp = copy.deepcopy(obj)
        form = ElementGroupForm(data=request.POST, instance=obj_temp)
        try:
            element_list = json.loads(request.POST.get('element', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            element_list = None
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = obj.creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            form.save_m2m()
            if element_list is not None:
                objects = Element.objects.filter(element_group=obj)
                object_values = objects.order_by('order').values('name', 'by', 'locator', 'description')
                object_values = list(object_values)
                if object_values != element_list:
                    objects.delete()
                    order = 0
                    for v in element_list:
                        if not v or v['name'] is None or v['name'].strip() == '':
                            continue
                        else:
                            order += 1
                            Element.objects.create(
                                element_group=obj, name=v['name'].strip(), by=v['by'], locator=v['locator'],
                                description=v['description'], order=order)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            if redirect:
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect(request.get_full_path())
        else:
            if element_list is not None:
                # 暂存element列表
                temp_dict = dict()
                temp_dict['data'] = element_list
                temp_list_json = json.dumps(temp_dict)

        return render(request, 'main/element_group/detail.html', locals())


@login_required
def add(request):
    next_ = request.GET.get('next', '/home/')
    by_list_json = json.dumps(Step.ui_by_list)
    if request.method == 'GET':
        form = ElementGroupForm()
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/element_group/detail.html', locals())
    elif request.method == 'POST':
        form = ElementGroupForm(data=request.POST)
        try:
            element_list = json.loads(request.POST.get('element', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            element_list = None
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = request.user
            form_.modifier = request.user
            form_.is_active = True
            form_.save()
            form.save_m2m()
            obj = form_
            pk = obj.id
            if element_list:
                order = 0
                for v in element_list:
                    if not v:
                        continue
                    order += 1
                    if v['name'] is None:
                        continue
                    else:
                        Element.objects.create(
                            element_group=obj, name=v['name'].strip(), by=v['by'], locator=v['locator'],
                            description=v['description'], order=order)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            if redirect == 'add_another':
                return HttpResponseRedirect(request.get_full_path())
            elif redirect:
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect('{}?next={}'.format(reverse(detail, args=[pk]), quote(next_)))
        else:
            if element_list:
                # 暂存element列表
                temp_dict = dict()
                temp_dict['data'] = element_list
                temp_list_json = json.dumps(temp_dict)

        return render(request, 'main/element_group/detail.html', locals())


@login_required
def delete(request, pk):
    if request.method == 'POST':
        ElementGroup.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


@login_required
def multiple_delete(request):
    if request.method == 'POST':
        try:
            pk_list = json.loads(request.POST['pk_list'])
            ElementGroup.objects.filter(pk__in=pk_list, creator=request.user).update(
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
            obj = ElementGroup.objects.get(pk=pk)
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


# 获取元素组中的元素
@login_required
def elements(_, pk):
    objects = Element.objects.filter(element_group=pk).order_by('order').values(
        'pk', 'uuid', 'name', 'by', 'locator', 'description')
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': list(objects)})


# 获取带搜索信息的下拉列表数据
@login_required
def select_json(request):
    condition = request.POST.get('condition', '{}')
    try:
        condition = json.loads(condition)
    except json.decoder.JSONDecodeError:
        condition = dict()
    selected_pk = condition.get('selected_pk')
    # objects = ElementGroup.objects.filter(is_active=True).values('pk').annotate(name_=Concat(
    #     'pk', Value(' | '), 'name', Value(' | '), 'keyword', Value(' | '), 'project__name', output_field=CharField()),
    # )
    objects = ElementGroup.objects.filter(is_active=True).values('pk', 'uuid', 'name', 'keyword', 'project__name')

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


# 复制操作
def copy_action(pk, user, name_prefix=None):
    obj = ElementGroup.objects.get(pk=pk)
    sub_object_values = list(
        Element.objects.filter(element_group=obj).order_by('order').values('name', 'by', 'locator', 'description'))
    obj.pk = None
    if name_prefix:
        obj.name = name_prefix + obj.name
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
            Element.objects.create(
                element_group=obj, name=v['name'].strip(), by=v['by'], locator=v['locator'],
                description=v['description'], order=order)
    return obj


# 复制
@login_required
def copy_(request, pk):
    name_prefix = request.POST.get('name_prefix', '')
    try:
        obj = copy_action(pk, request.user, name_prefix)
        return JsonResponse({
            'statue': 1, 'message': 'OK', 'data': {
                'new_pk': obj.pk, 'new_url': reverse(detail, args=[obj.pk])}
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
            for pk in pk_list:
                _ = copy_action(pk, request.user, name_prefix)
        except Exception as e:
            return JsonResponse({'statue': 2, 'message': str(e), 'data': None})
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk_list})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': []})


# 获取调用列表
def reference(request, pk):
    try:
        obj = ElementGroup.objects.get(pk=pk)
    except ElementGroup.DoesNotExist:
        raise Http404('ElementGroup does not exist')
    objects = Suite.objects.filter(is_active=True, element_group=obj).order_by('-modified_date').values(
        'pk', 'uuid', 'name', 'keyword', 'creator', 'creator__username', 'modified_date').annotate(
        real_name=Concat('creator__last_name', 'creator__first_name', output_field=CharField()))
    for obj_ in objects:
        obj_['url'] = '{}?next={}'.format(reverse(suite.detail, args=[obj_['pk']]), reverse(suite.list_))
        obj_['type'] = '套件'
    objects = list(objects)

    return render(request, 'main/include/detail_reference.html', locals())

