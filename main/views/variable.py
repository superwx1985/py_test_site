import json
import traceback
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render, get_object_or_404
from django.core.serializers import serialize
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db import connection
from django.db.models import Q, F, CharField, Value
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core import serializers
from main.models import VariableGroup, Variable
from main.forms import PaginatorForm, VariableGroupForm
from main.views.general import get_query_condition


@login_required
def variable_groups(request):
    if request.method == 'POST':
        page = int(request.POST.get('page', 1)) if request.POST.get('page') != '' else 1
        size = int(request.POST.get('size', 5)) if request.POST.get('size') != '' else 10
        search_text = str(request.POST.get('search_text', ''))
    else:
        page = int(request.COOKIES.get('page', 1))
        size = int(request.COOKIES.get('size', 10))
        search_text = ''
        if request.session.get('status', None) == 'success':
            is_success = True
        request.session['status'] = None
    keyword_list_temp = search_text.split(' ')
    keyword_list = list()
    for keyword in keyword_list_temp:
        if keyword.strip() != '':
            keyword_list.append(keyword)
    q = get_query_condition(keyword_list)
    objects = VariableGroup.objects.filter(q, is_active=1).order_by('id')
    paginator = Paginator(objects, size)
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
        page = 1
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    paginator_form = PaginatorForm(initial={'page': page, 'size': size}, page_max_value=paginator.num_pages)
    return render(request, 'main/variable/list.html', locals())


@login_required
def variable_group(request, pk):
    try:
        obj = VariableGroup.objects.select_related('creator', 'modifier').get(pk=pk)
    except VariableGroup.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        form = VariableGroupForm(instance=obj)
        if request.session.get('status', None) == 'success':
            is_success = True
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER'))
        return render(request, 'main/variable/detail.html', locals())
    elif request.method == 'POST':
        creator = obj.creator
        form = VariableGroupForm(data=request.POST, instance=obj)
        variable_list = json.loads(request.POST.get('variable', '[]'))
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            form.save_m2m()
            vo = Variable.objects.filter(variable_group=obj)
            vv = vo.order_by('order').values('name', 'value')
            vv = list(vv)
            if vv != variable_list:
                vo.delete()
                order = 0
                for v in variable_list:
                    if not v:
                        continue
                    order += 1
                    Variable.objects.create(variable_group=obj, name=v['name'], value=v['value'], order=order)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('variable_group', args=[pk]) + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        else:
            # 暂存variable列表
            temp_dict = dict()
            temp_dict['data'] = variable_list
            temp_list_json = json.dumps(temp_dict)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/variable/detail.html', locals())


@login_required
def variable_group_add(request):
    if request.method == 'GET':
        form = VariableGroupForm()
        if request.session.get('status', None) == 'success':
            is_success = True
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER'))
        return render(request, 'main/variable/detail.html', locals())
    elif request.method == 'POST':
        form = VariableGroupForm(data=request.POST)
        variable_list = json.loads(request.POST.get('variable', '[]'))
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = request.user
            form_.modifier = request.user
            form_.is_active = True
            form_.save()
            form.save_m2m()
            pk = form_.id
            order = 0
            for v in variable_list:
                if not v:
                    continue
                order += 1
                Variable.objects.create(variable_group=pk, name=v['name'], value=v['value'], order=order)
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
            # 暂存variable列表
            temp_dict = dict()
            temp_dict['data'] = variable_list
            temp_list_json = json.dumps(temp_dict)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/variable/detail.html', locals())


@login_required
def variable_group_delete(request, pk):
    if request.method == 'POST':
        VariableGroup.objects.filter(pk=pk).update(is_active=0, modifier=request.user, modified_date=timezone.now())
        return HttpResponse('success')
    else:
        return HttpResponseBadRequest('only accept "POST" method')


@login_required
def variable_group_update(request, pk):
    if request.method == 'POST':
        response_ = {'new_value': ''}
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            response_['new_value'] = new_value
            obj = VariableGroup.objects.get(pk=pk)
            obj.modifier = request.user
            obj.modified_date = timezone.now()
            if col_name == 'name':
                obj.name = new_value
                obj.clean_fields()
                obj.save()
            elif col_name == 'keyword':
                obj.keyword = new_value
                obj.clean_fields()
                obj.save()
            else:
                raise ValueError('invalid col_name')
        except Exception as e:
            print(traceback.format_exc())
            return HttpResponseBadRequest(str(e))
        return JsonResponse(response_)
    else:
        return HttpResponseBadRequest('only accept "POST" method')


# 获取变量组中的变量
@login_required
def variable_group_variables(request, pk):
    v = Variable.objects.filter(variable_group=pk).order_by('order').values('pk', 'name', 'value')
    data_dict = dict()
    data_dict['data'] = list(v)
    return JsonResponse(data_dict)
