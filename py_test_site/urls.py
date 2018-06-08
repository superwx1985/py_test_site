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

from django.contrib import admin
from django.urls import path
import main.views.general as general
import main.views.case as case
import main.views.step as step
import main.views.config as config
import main.views.variable as variable


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('run/', general.run, name='run'),

    path('cases/', case.cases, name='cases'),
    path('case/add/', case.case_add, name='case_add'),
    path('case/<int:pk>/', case.case, name='case'),
    path('case/<int:pk>/delete/', case.case_delete, name='case_delete'),
    path('case/<int:pk>/update/', case.case_update, name='case_update'),
    path('case/<int:pk>/steps/', case.case_steps, name='case_steps'),

    path('steps/', step.steps, name='steps'),
    path('step/add/', step.step_add, name='step_add'),
    path('step/<int:pk>/', step.step, name='step'),
    path('step/<int:pk>/delete/', step.step_delete, name='step_delete'),
    path('step/<int:pk>/update/', step.step_update, name='step_update'),
    path('step/list_all/', step.step_list_all, name='step_list_all'),
    path('step/list_temp/', step.step_list_temp, name='step_list_temp'),

    path('configs/', config.configs, name='configs'),
    path('config/add/', config.config_add, name='config_add'),
    path('config/<int:pk>/', config.config, name='config'),
    path('config/<int:pk>/delete/', config.config_delete, name='config_delete'),
    path('config/<int:pk>/update/', config.config_update, name='config_update'),

    path('variable_groups/', variable.variable_groups, name='variable_groups'),
    path('variable_group/add/', variable.variable_group_add, name='variable_group_add'),
    path('variable_group/<int:pk>/', variable.variable_group, name='variable_group'),
    path('variable_group/<int:pk>/delete/', variable.variable_group_delete, name='variable_group_delete'),
    path('variable_group/<int:pk>/update/', variable.variable_group_update, name='variable_group_update'),
    path('variable_group/<int:pk>/variables/', variable.variable_group_variables, name='variable_group_variables'),

    path('test1/', general.test1, name='test1'),
    path('test2/', general.test2, name='test2'),
    path('logout/', general.logout, name='logout'),

]

