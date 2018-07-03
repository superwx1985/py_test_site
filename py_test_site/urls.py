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

from django.urls import path
from django.conf.urls.static import static
from . import settings
from django.contrib import admin
import main.views.general as general
import main.views.case as case
import main.views.step as step
import main.views.config as config
import main.views.variable as variable
import main.views.suite as suite
import main.views.result as result


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),

    path('home/', case.cases, name='home'),
    path('', case.cases),

    path('cases/', case.cases, name='cases'),
    path('case/add/', case.case_add, name='case_add'),
    path('case/<int:pk>/', case.case, name='case'),
    path('case/<int:pk>/delete/', case.case_delete, name='case_delete'),
    path('case/<int:pk>/quick_update/', case.case_quick_update, name='case_quick_update'),
    path('case/<int:pk>/steps/', case.case_steps, name='case_steps'),
    path('case/list_all/', case.case_list, name='case_list'),
    path('case/list_temp/', case.case_list_temp, name='case_list_temp'),

    path('steps/', step.list_, name='steps'),
    path('step/add/', step.add, name='step_add'),
    path('step/<int:pk>/', step.detail, name='step'),
    path('step/<int:pk>/delete/', step.delete, name='step_delete'),
    path('step/<int:pk>/quick_update/', step.quick_update, name='step_quick_update'),
    path('step/<int:pk>/copy/', step.copy, name='step_copy'),
    path('step/list_json/', step.list_json, name='step_list_json'),
    path('step/list_temp/', step.list_temp, name='step_list_temp'),

    path('configs/', config.configs, name='configs'),
    path('config/add/', config.config_add, name='config_add'),
    path('config/<int:pk>/', config.config, name='config'),
    path('config/<int:pk>/delete/', config.config_delete, name='config_delete'),
    path('config/<int:pk>/quick_update/', config.config_quick_update, name='config_quick_update'),

    path('variable_groups/', variable.variable_groups, name='variable_groups'),
    path('variable_group/add/', variable.variable_group_add, name='variable_group_add'),
    path('variable_group/<int:pk>/', variable.variable_group, name='variable_group'),
    path('variable_group/<int:pk>/delete/', variable.variable_group_delete, name='variable_group_delete'),
    path('variable_group/<int:pk>/quick_update/', variable.variable_group_quick_update, name='variable_group_quick_update'),
    path('variable_group/<int:pk>/variables/', variable.variable_group_variables, name='variable_group_variables'),

    path('suites/', suite.suites, name='suites'),
    path('suite/add/', suite.suite_add, name='suite_add'),
    path('suite/<int:pk>/', suite.suite, name='suite'),
    path('suite/<int:pk>/delete/', suite.suite_delete, name='suite_delete'),
    path('suite/<int:pk>/quick_update/', suite.suite_quick_update, name='suite_quick_update'),
    path('suite/<int:pk>/cases/', suite.suite_cases, name='suite_cases'),
    path('suite/<int:pk>/execute/', suite.suite_execute, name='suite_execute'),

    path('results/', result.results, name='results'),
    path('result/<int:pk>/', result.result, name='result'),
    path('result/<int:pk>/delete/', result.result_delete, name='result_delete'),
    path('result/<int:pk>/quick_update/', result.result_quick_update, name='result_quick_update'),

    path('step_img/<int:pk>/', result.step_img, name='step_img'),

    path('logout/', general.logout, name='logout'),

    path('debug/', general.debug, name='debug'),
    path('test1/', general.test1, name='test1'),
    path('test2/', general.test2, name='test2'),
    path('debug1/', general.debug1, name='debug1'),
]

# 添加media文件映射
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
