import json
import logging
import copy
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
from main.models import Config
from main.forms import OrderByForm, PaginatorForm, ConfigForm
from main.views.general import get_query_condition, change_to_positive_integer

logger = logging.getLogger('django.request')


@login_required
def list_(request):
    if request.method == 'POST':
        page = request.POST.get('page')
        size = request.POST.get('size')
        search_text = request.POST.get('search_text')
        order_by = request.POST.get('order_by')
        order_by_reverse = request.POST.get('order_by_reverse')
        own = request.POST.get('own')
    else:
        page = request.COOKIES.get('page')
        size = request.COOKIES.get('size')
        search_text = request.COOKIES.get('search_text')
        order_by = request.COOKIES.get('order_by')
        order_by_reverse = request.COOKIES.get('order_by_reverse')
        own = request.COOKIES.get('own')

    page = change_to_positive_integer(page)
    size = change_to_positive_integer(size, 10)
    search_text = str(search_text) if search_text else ''
    if order_by is None or order_by == '':
        order_by = 'modified_date'
    if order_by_reverse is None or order_by_reverse == '' or order_by_reverse == 'False':
        order_by_reverse = False
    else:
        order_by_reverse = True
    if own is None or own == '' or own == 'False':
        own = False
    else:
        own = True

    if request.session.get('status', None) == 'success':
        prompt = 'success'
    request.session['status'] = None
    q = get_query_condition(search_text)
    if own:
        objects = Config.objects.filter(q, is_active=True, creator=request.user).values(
            'pk', 'name', 'keyword', 'creator', 'creator__username', 'modified_date')
    else:
        objects = Config.objects.filter(q, is_active=True).values(
            'pk', 'name', 'keyword', 'creator', 'creator__username', 'modified_date')
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
    return render(request, 'main/config/list.html', locals())


@login_required
def detail(request, pk):
    try:
        obj = Config.objects.select_related('creator', 'modifier').get(pk=pk)
    except Config.DoesNotExist:
        raise Http404('Step does not exist')
    if request.method == 'GET':
        form = ConfigForm(instance=obj)
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/config/detail.html', locals())
    elif request.method == 'POST':
        obj_temp = copy.deepcopy(obj)
        form = ConfigForm(data=request.POST, instance=obj_temp)
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = obj.creator
            form_.modifier = request.user
            form_.is_active = obj.is_active
            form_.save()
            form.save_m2m()
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('config', args=[pk]) + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/config/detail.html', locals())


@login_required
def add(request):
    if request.method == 'GET':
        form = ConfigForm()
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/config/detail.html', locals())
    elif request.method == 'POST':
        form = ConfigForm(data=request.POST)
        if form.is_valid():
            form_ = form.save(commit=False)
            form_.creator = request.user
            form_.modifier = request.user
            form_.is_active = True
            form_.save()
            form.save_m2m()
            pk = form_.id
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            redirect_url = request.POST.get('redirect_url', '')
            if not redirect or not redirect_url:
                return HttpResponseRedirect(reverse('config', args=[pk]) + '?redirect_url=' + redirect_url)
            elif redirect == 'add_another':
                return HttpResponseRedirect(reverse('config_add') + '?redirect_url=' + redirect_url)
            else:
                return HttpResponseRedirect(redirect_url)
        redirect_url = request.POST.get('redirect_url', '')
        is_success = False
        return render(request, 'main/config/detail.html', locals())


@login_required
def delete(request, pk):
    if request.method == 'POST':
        Config.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


@login_required
def quick_update(request, pk):
    if request.method == 'POST':
        try:
            col_name = request.POST['col_name']
            new_value = request.POST['new_value']
            obj = Config.objects.get(pk=pk)
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


@login_required
def list_json_all(request):
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': 1})
