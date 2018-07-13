import json
import logging
import copy
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.db.models import F, CharField, Value, Count
from django.db.models.functions import Concat
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from main.models import Case, Step, CaseVsStep
from main.forms import OrderByForm, PaginatorForm, CaseForm
from main.views.general import get_query_condition, change_to_positive_integer, Cookie
from urllib.parse import quote

logger = logging.getLogger('django.request')


# 用例列表
@login_required
def list_(request):
    # if request.method == 'POST':
    #     page = request.GET.get('page', 1)
    #     size = request.GET.get('size', 10)
    #     search_text = request.GET.get('search_text', '')
    #     order_by = request.GET.get('order_by', 'modified_date')
    #     order_by_reverse = request.GET.get('order_by_reverse', 'on')
    #     own = request.GET.get('own', 'on')
    # else:
    #     page = request.COOKIES.get('page')
    #     size = request.COOKIES.get('size')
    #     search_text = request.COOKIES.get('search_text')
    #     order_by = request.COOKIES.get('order_by')
    #     order_by_reverse = request.COOKIES.get('order_by_reverse')
    #     own = request.COOKIES.get('own')
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
        objects = Case.objects.filter(q, is_active=True).values(
            'pk', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date')
    else:
        objects = Case.objects.filter(q, is_active=True, creator=request.user).values(
            'pk', 'name', 'keyword', 'project__name', 'creator', 'creator__username', 'modified_date')
    objects2 = Case.objects.filter(is_active=True, step__is_active=True).values('pk').annotate(m2m_count=Count('step'))
    count_ = {o['pk']: o['m2m_count'] for o in objects2}
    for o in objects:
        o['m2m_count'] = count_.get(o['pk'], 0)
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
                            m2m_object = Step.objects.get(pk=m2m_pk)
                        except Step.DoesNotExist:
                            logger.warning('找不到 m2m_object [{}]'.format(m2m_pk), exc_info=True)
                            continue
                        order += 1
                        CaseVsStep.objects.create(case=obj, step=m2m_object, order=order, creator=request.user,
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

        is_success = False
        return render(request, 'main/case/detail.html', locals())


@login_required
def add(request):
    next_ = request.GET.get('next', '/home/')
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
                        m2m_object = Step.objects.get(pk=m2m_pk)
                    except Step.DoesNotExist:
                        logger.warning('找不到 m2m_object [{}]'.format(m2m_pk), exc_info=True)
                        continue
                    order += 1
                    CaseVsStep.objects.create(case=obj, step=m2m_object, order=order, creator=request.user,
                                              modifier=request.user)
            request.session['status'] = 'success'
            redirect = request.POST.get('redirect')
            if redirect == 'add_another':
                return HttpResponseRedirect(request.get_full_path())
            elif redirect:
                return HttpResponseRedirect(next_)
            else:
                return HttpResponseRedirect('{}?next={}'.format(reverse(detail, args=[pk]), quote(next_)))
            #
            # if not redirect or not redirect_url:
            #     return HttpResponseRedirect(reverse('case', args=[pk]) + '?redirect_url=' + redirect_url)
            # elif redirect == 'add_another':
            #     return HttpResponseRedirect(reverse('case_add') + '?redirect_url=' + redirect_url)
            # else:
            #     return HttpResponseRedirect(redirect_url)
        else:
            if m2m_list is not None:
                temp_list_json = json.dumps(m2m_list)

        is_success = False
        return render(request, 'main/case/detail.html', locals())


@login_required
def delete(request, pk):
    if request.method == 'POST':
        Case.objects.filter(pk=pk).update(is_active=False, modifier=request.user, modified_date=timezone.now())
        return JsonResponse({'statue': 1, 'message': 'OK', 'data': pk})
    else:
        return JsonResponse({'statue': 2, 'message': 'Only accept "POST" method', 'data': pk})


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
def steps(request, pk):
    objects = Step.objects.filter(case=pk, is_active=True).order_by('casevsstep__order').values(
        'pk', 'name', 'keyword', 'project__name', order=F('casevsstep__order')).annotate(
        action=Concat('action__name', Value(' - '), 'action__type__name', output_field=CharField()))
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': list(objects)})


# 获取待选
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
    order_by = condition.get('order_by', 'name')
    order_by_reverse = condition.get('order_by_reverse', 'False')
    all_ = condition.get('all_', 'False')

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

    q = get_query_condition(search_text)
    if all_:
        objects = Case.objects.filter(q, is_active=True).order_by('pk').values(
            'pk', 'name', 'keyword', 'project__name')
    else:
        objects = Case.objects.filter(q, is_active=True, creator=request.user).order_by('pk').values('pk', 'name', 'keyword', 'project__name')
    # 排序
    if objects:
        if order_by not in objects[0]:
            order_by = 'name'
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
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': {
        'objects': list(objects), 'page': page, 'max_page': paginator.num_pages, 'size': size}})


# 获取临时case
@login_required
def case_list_temp(request):
    list_ = json.loads(request.POST.get('condition', ''))
    order = 0
    list_temp = list()
    for pk in list_:
        if pk is None or pk.strip() == '':
            continue
        order += 1
        objects = Case.objects.filter(pk=pk).values('pk', 'name')
        objects = list(objects)
        objects[0]['order'] = order
        list_temp.append(objects[0])
    return JsonResponse({'statue': 1, 'message': 'OK', 'data': list_temp})
