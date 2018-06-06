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

from django.contrib import admin, auth
from django.urls import path
import main.views as mv
import main.config.views as config_views
import main.variable.views as variable_views


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('run/', mv.run, name='run'),

    path('cases/', mv.cases, name='cases'),
    path('case/add/', mv.case_add, name='case_add'),
    path('case/<int:pk>/', mv.case, name='case'),
    path('case/<int:pk>/delete/', mv.case_delete, name='case_delete'),
    path('case/<int:pk>/update/', mv.case_update, name='case_update'),
    path('case/<int:pk>/steps/', mv.case_steps, name='case_steps'),

    path('steps/', mv.steps, name='steps'),
    path('step/add/', mv.step_add, name='step_add'),
    path('step/<int:pk>/', mv.step, name='step'),
    path('step/<int:pk>/delete/', mv.step_delete, name='step_delete'),
    path('step/<int:pk>/update/', mv.step_update, name='step_update'),
    path('step/list_all/', mv.step_list_all, name='step_list_all'),
    path('step/list_temp/', mv.step_list_temp, name='step_list_temp'),

    path('configs/', config_views.configs, name='configs'),
    path('config/add/', config_views.config_add, name='config_add'),
    path('config/<int:pk>/', config_views.config, name='config'),
    path('config/<int:pk>/delete/', config_views.config_delete, name='config_delete'),
    path('config/<int:pk>/update/', config_views.config_update, name='config_update'),

    path('variable_groups/', variable_views.variable_groups, name='variable_groups'),
    path('variable_group/add/', variable_views.variable_group_add, name='variable_group_add'),
    path('variable_group/<int:pk>/', variable_views.variable_group, name='variable_group'),
    path('variable_group/<int:pk>/delete/', variable_views.variable_group_delete, name='variable_group_delete'),
    path('variable_group/<int:pk>/update/', variable_views.variable_group_update, name='variable_group_update'),
    path('variable_group/<int:pk>/variables/', variable_views.variable_group_variables, name='variable_group_variables'),

    path('action_list/', mv.action_list, name='action_list'),
    path('test1/', mv.test1, name='test1'),
    path('test2/', mv.test2, name='test2'),
    path('logout/', mv.logout, name='logout'),

]

