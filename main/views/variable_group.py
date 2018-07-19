import json
import logging
import copy
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import VariableGroup, Variable
from main.forms import OrderByForm, PaginatorForm, VariableGroupForm
from main.views.general import get_query_condition, change_to_positive_integer, Cookie
from urllib.parse import quote

logger = logging.getLogger('django.request')


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
    objects = VariableGroup.objects.filter(q).values(
        'pk', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date').annotate(
        variable_count=Count('variable'))
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
    respond = render(request, 'main/variable_group/list.html', locals())
    for cookie in cookies:
        respond.set_cookie(cookie.key, cookie.value, cookie.max_age, cookie.expires, cookie.path)
    return respond


@login_required
def detail(request, pk):
    next_ = request.GET.get('next', '/home/')
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
            if redirect:
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect(request.get_full_path())
        else:
            if variable_list is not None:
                # 暂存variable列表
                temp_dict = dict()
                temp_dict['data'] = variable_list
                temp_list_json = json.dumps(temp_dict)

        is_success = False
        return render(request, 'main/variable_group/detail.html', locals())


@login_required
def add(request):
    next_ = request.GET.get('next', '/home/')
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
            if redirect == 'add_another':
                return HttpResponseRedirect(request.get_full_path())
            elif redirect:
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect('{}?next={}'.format(reverse(detail, args=[pk]), quote(next_)))
        else:
            if variable_list:
                # 暂存variable列表
                temp_dict = dict()
                temp_dict['data'] = variable_list
                temp_list_json = json.dumps(temp_dict)

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
def variables(_, pk):
    objects = Variable.objects.filter(variable_group=pk).order_by('order').values('pk', 'name', 'value')
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': list(objects)})


@login_required
def select_json(request):
    condition = request.POST.get('condition', '{}')
    try:
        condition = json.loads(condition)
    except json.decoder.JSONDecodeError:
        condition = dict()
    selected_pk = condition.get('selected_pk')
    # objects = VariableGroup.objects.filter(is_active=True).values('pk').annotate(name_=Concat(
    #     'pk', Value(' | '), 'name', Value(' | '), 'keyword', Value(' | '), 'project__name', output_field=CharField()),
    # )
    objects = VariableGroup.objects.filter(is_active=True).values('pk', 'name', 'project__name', 'keyword')

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
        data.append(d)

    return JsonResponse({'statue': 1, 'message': 'OK', 'data': data})
