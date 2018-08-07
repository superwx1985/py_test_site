import logging
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from main.forms import LoginForm, UserForm
from django.contrib.auth.models import User
from django.conf import settings

logger = logging.getLogger('django.request')


def login(request):
    redirect_url = request.GET.get('next', reverse('home'))
    site_name = settings.SITE_NAME
    site_version = settings.SITE_VERSION
    if redirect_url == reverse('user_logout'):
        redirect_url = reverse('home')
    if request.user.is_authenticated:
        return HttpResponseRedirect(redirect_url)
    cookies = list()
    delete_cookies = list()
    response = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
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
        form = LoginForm(initial={'remember_me': False})

    response = render(request, 'main/user/login.html', locals()) if not response else response
    for cookie in cookies:
        response.set_cookie(cookie.key, cookie.value, max_age=cookie.max_age, expires=cookie.expires, path=cookie.path)
    for cookie in delete_cookies:
        response.delete_cookie(cookie)
    return response


# 跟目录跳转，防止直接使用根目录，污染cookie
def login_redirect(_):
    return HttpResponseRedirect(reverse('user_login'))


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('home')))


@login_required
def detail(request):
    inside = request.GET.get('inside')
    obj = request.user
    pk = obj.pk
    if request.method == 'GET':
        form = UserForm(obj, initial={
            'first_name': obj.first_name,
            'last_name': obj.last_name,
        })
        if request.session.get('status', None) == 'success':
            prompt = 'success'
        request.session['status'] = None
        redirect_url = request.GET.get('redirect_url', request.META.get('HTTP_REFERER', '/home/'))
        return render(request, 'main/user/detail.html', locals())

    elif request.method == 'POST':
        form = UserForm(obj, request.POST)
        if form.is_valid():
            obj.first_name = form.cleaned_data.get('first_name', '')
            obj.last_name = form.cleaned_data.get('last_name', '')

            original_password = form.cleaned_data.get('original_password')
            new_password = form.cleaned_data.get('new_password')

            if new_password:
                if obj.check_password(original_password):
                    obj.set_password(new_password)
                    obj.save()
                    auth.login(request, obj)
                    request.session['status'] = 'success'
                    return HttpResponseRedirect(request.get_full_path())
                else:
                    form.add_error('original_password', '原密码不正确')
            else:
                obj.save()
                request.session['status'] = 'success'
                return HttpResponseRedirect(request.get_full_path())

        return render(request, 'main/user/detail.html', locals())
