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
import main.views.user as user
import main.views.case as case
import main.views.step as step
import main.views.config as config
import main.views.variable_group as variable_group
import main.views.suite as suite
import main.views.result as result


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),

    path('', user.login_redirect),
    path('user/login/', user.login, name='user_login'),
    path('user/logout/', user.logout, name='user_logout'),
    path('user/', user.detail, name='user'),

    path('home/', result.list_, name='home'),

    path('cases/', case.list_, name='cases'),
    path('case/add/', case.add, name='case_add'),
    path('case/list_json/', case.list_json, name='case_list_json'),
    path('case/list_temp/', case.list_temp, name='case_list_temp'),
    path('case/select_json/', case.select_json, name='case_select_json'),
    path('case/<str:pk>/', case.detail, name='case'),
    path('case/<str:pk>/delete/', case.delete, name='case_delete'),
    path('case/<str:pk>/quick_update/', case.quick_update, name='case_quick_update'),
    path('case/<str:pk>/steps/', case.steps, name='case_steps'),
    path('case/<str:pk>/copy/', case.copy_, name='case_copy'),
    path('case/<str:pk>/reference/', case.reference, name='case_reference'),

    path('steps/', step.list_, name='steps'),
    path('step/add/', step.add, name='step_add'),
    path('step/list_json/', step.list_json, name='step_list_json'),
    path('step/list_temp/', step.list_temp, name='step_list_temp'),
    path('step/<str:pk>/', step.detail, name='step'),
    path('step/<str:pk>/delete/', step.delete, name='step_delete'),
    path('step/<str:pk>/quick_update/', step.quick_update, name='step_quick_update'),
    path('step/<str:pk>/copy/', step.copy_, name='step_copy'),
    path('step/<str:pk>/reference/', step.reference, name='step_reference'),

    path('configs/', config.list_, name='configs'),
    path('config/add/', config.add, name='config_add'),
    path('config/select_json/', config.select_json, name='config_select_json'),
    path('config/<str:pk>/', config.detail, name='config'),
    path('config/<str:pk>/delete/', config.delete, name='config_delete'),
    path('config/<str:pk>/quick_update/', config.quick_update, name='config_quick_update'),
    path('config/<str:pk>/reference/', config.reference, name='config_reference'),

    path('variable_groups/', variable_group.list_, name='variable_groups'),
    path('variable_group/add/', variable_group.add, name='variable_group_add'),
    path('variable_group/select_json/', variable_group.select_json, name='variable_group_select_json'),
    path('variable_group/<str:pk>/', variable_group.detail, name='variable_group'),
    path('variable_group/<str:pk>/delete/', variable_group.delete, name='variable_group_delete'),
    path('variable_group/<str:pk>/quick_update/', variable_group.quick_update, name='variable_group_quick_update'),
    path('variable_group/<str:pk>/variables/', variable_group.variables, name='variable_group_variables'),
    path('variable_group/<str:pk>/reference/', variable_group.reference, name='variable_group_reference'),

    path('suites/', suite.list_, name='suites'),
    path('suite/add/', suite.add, name='suite_add'),
    path('suite/<str:pk>/', suite.detail, name='suite'),
    path('suite/<str:pk>/delete/', suite.delete, name='suite_delete'),
    path('suite/<str:pk>/quick_update/', suite.quick_update, name='suite_quick_update'),
    path('suite/<str:pk>/cases/', suite.cases, name='suite_cases'),
    # path('suite/<str:pk>/execute/', suite.execute_, name='suite_execute'),
    path('ws/suite_execute/<int:suite_pk>', suite.execute_, name='suite_execute'),

    path('results/', result.list_, name='results'),
    path('result/<str:pk>/', result.detail, name='result'),
    path('result/<str:pk>/delete/', result.delete, name='result_delete'),
    path('result/<str:pk>/quick_update/', result.quick_update, name='result_quick_update'),

    path('step_result/<str:pk>/json', result.step_result_json, name='step_result_json'),



    path('debug/', general.debug, name='debug'),
    path('test1/', general.test1, name='test1'),
    path('test2/', general.test2, name='test2'),
    path('debug1/', general.debug1, name='debug1'),
    path('debug2/', general.debug2, name='debug2'),
]

# 添加media文件映射
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
