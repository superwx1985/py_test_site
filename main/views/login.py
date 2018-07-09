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
from django.contrib.auth.models import User
from main.forms import UserForm
from main.views.general import get_query_condition, change_to_positive_integer, Cookie

logger = logging.getLogger('django.request')


def login(request):
    redirect_url = request.GET.get('next', reverse('home'))
    if redirect_url == reverse('logout'):
        redirect_url = reverse('home')
    if request.user.is_authenticated:
        return HttpResponseRedirect(redirect_url)
    cookies = list()
    delete_cookies = list()
    response = None
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                if remember_me:
                    # cookies.append(Cookie('remember_me', 'on', max_age=30*24*3600, path=request.path))
                    # cookies.append(Cookie('username', username, max_age=30*24*3600, path=request.path))
                    # cookies.append(Cookie('password', password, max_age=30*24*3600, path=request.path))
                    request.session.set_expiry(30*24*3600)  # 登录信息默认30天过期
                else:
                    # delete_cookies.append('remember_me')
                    # delete_cookies.append('username')
                    # delete_cookies.append('password')
                    request.session.set_expiry(0)  # 不保留登录信息
                request.session['user'] = username
                response = HttpResponseRedirect(redirect_url)
            else:
                error_msg = '账号或密码错误'

    else:
        # remember_me = request.COOKIES.get('remember_me', 'off')
        # if remember_me == 'on':
        #     remember_me = True
        # else:
        #     remember_me = False
        form = UserForm(initial={'remember_me': False})

    response = render(request, 'main/login/login.html', locals()) if not response else response
    for cookie in cookies:
        response.set_cookie(cookie.key, cookie.value, max_age=cookie.max_age, expires=cookie.expires, path=cookie.path)
    for cookie in delete_cookies:
        response.delete_cookie(cookie)
    return response


# 跟目录跳转，防止直接使用根目录，污染cookie
def login_redirect(_):
    return HttpResponseRedirect(reverse('login'))


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('home')))