"""py_test_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin, auth
import main.views as mv


urlpatterns = [
    url('^admin/', admin.site.urls, name='admin'),
    url('^run/$', mv.run, name='run'),
    url('^cases/$', mv.cases, name='cases'),
    url('^case/$', mv.case, name='case'),
    url('^case/delete/$', mv.case_delete, name='case_delete'),
    url('^case/update/$', mv.case_update, name='case_update'),

    url('^steps/$', mv.steps, name='steps'),
    url('^step/$', mv.step, name='step'),
    url('^step/delete/$', mv.step_delete, name='step_delete'),
    url('^step/update/$', mv.step_update, name='step_update'),
    url('^step/update_all/$', mv.step_update_all, name='step_update_all'),

    url('^action_list/$', mv.action_list, name='action_list'),

]

