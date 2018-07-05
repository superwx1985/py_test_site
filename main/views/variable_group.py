import json
import logging
import copy
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render, get_object_or_404
from django.core.serializers import serialize
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db import connection
from django.db.models import Q, F, CharField, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core import serializers
from main.models import VariableGroup, Variable
from main.forms import OrderByForm, PaginatorForm, VariableGroupForm
from main.views.general import get_query_condition

logger = logging.getLogger('django.request')


@login_required
def list_(request):
    if request.method == 'POST':
        page = int(request.POST.get('page', 1)) if request.POST.get('page') != '' else 1
        if page <= 0:
            page = 1
        size = int(request.POST.get('size', 5)) if request.POST.get('size') != '' else 10
        search_text = str(request.POST.get('search_text', ''))
        order_by = request.POST.get('order_by', 'modified_date')
        order_by_reverse = request.POST.get('order_by_reverse', False)
        own = request.POST.get('own_checkbox')
    else:
        page = int(request.COOKIES.get('page', 1))
        size = int(request.COOKIES.get('size', 10))
        search_text = ''
        order_by = 'modified_date'
        order_by_reverse = True
        own = True
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
    q = get_query_condition(search_text)
    if own:
        objects = VariableGroup.objects.filter(q, is_active=True, creator=request.user).values(
            'pk', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
            variable_count=Count('variable'))
    else:
        objects = VariableGroup.objects.filter(q, is_active=True).values(
            'pk', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
            variable_count=Count('variable'))
    # 排序
    if objects:
        if order_by not in objects[0]:
            order_by = 'modified_date'
        if order_by_reverse is True or order_by_reverse == 'True':
            order_by_reverse = True
        else:
            order_by_reverse = False
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
    return render(request, 'main/variable_group/list.html', locals())


@login_required
def detail(request, pk):
    try:
        obj = VariableGroup.objects.select_related('creator', 'modifier').get(pk=pk)
    except VariableGroup.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        form = VariableGroupForm(instance=obj)
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/variable_group/detail.html', locals())
    elif request.method == 'POST':
        obj_temp = copy.deepcopy(obj)
        form = VariableGroupForm(data=request.POST, instance=obj_temp)
        variable_list = json.loads(request.POST.get('variable', '[]'))
        try:
            variable_list = json.loads(request.POST.get('variable', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            variable_list = None
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = obj.creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            form.save_m2m()
            if variable_list is not None:
                objects = Variable.objects.filter(variable_group=obj)
                object_values = objects.order_by('order').values('name', 'value')
                object_values = list(object_values)
                if object_values != variable_list:
                    objects.delete()
                    order = 0
                    for v in variable_list:
                        if not v or v['name'] is None or v['name'].strip() == '':
                            continue
                        else:
                            order += 1
                            Variable.objects.create(
                                variable_group=obj, name=v['name'].strip(), value=v['value'], order=order)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('variable_group', args=[pk]) + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        else:
            if variable_list is not None:
                # 暂存variable列表
                temp_dict = dict()
                temp_dict['data'] = variable_list
                temp_list_json = json.dumps(temp_dict)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/variable_group/detail.html', locals())


@login_required
def add(request):
    if request.method == 'GET':
        form = VariableGroupForm()
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/variable_group/detail.html', locals())
    elif request.method == 'POST':
        form = VariableGroupForm(data=request.POST)
        try:
            variable_list = json.loads(request.POST.get('variable', 'null'))
        except json.decoder.JSONDecodeError:
            logger.warning('无法获取m2m值', exc_info=True)
            variable_list = None
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = request.user
            form_.modifier = request.user
            form_.is_active = True
            form_.save()
            form.save_m2m()
            obj = form_
            pk = obj.id
            if variable_list:
                order = 0
                for v in variable_list:
                    if not v:
                        continue
                    order += 1
                    if v['name'] is None:
                        continue
                    else:
                        Variable.objects.create(
                            variable_group=obj, name=v['name'].strip(), value=v['value'], order=order)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('variable_group', args=[pk]) + '?redirect_url=' + redirect_url)
            elif redirect == 'add_another':
                return HttpResponseRedirect(reverse('variable_group_add') + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        else:
            if variable_list:
                # 暂存variable列表
                temp_dict = dict()
                temp_dict['data'] = variable_list
                temp_list_json = json.dumps(temp_dict)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/variable_group/detail.html', locals())


@login_required
def delete(request, pk):
    if request.method == 'POST':
        VariableGroup.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


@login_required
def quick_update(request, pk):
    if request.method == 'POST':
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            obj = VariableGroup.objects.get(pk=pk)
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


# 获取变量组中的变量
@login_required
def variables(request, pk):
    objects = Variable.objects.filter(variable_group=pk).order_by('order').values('pk', 'name', 'value')
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': list(objects)})
