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


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('run/', mv.run, name='run'),
    path('cases/', mv.cases, name='cases'),
    path('case/<int:object_id>/', mv.step, name='case'),
    path('case/add/', mv.step_add, name='case_add'),
    path('case/delete/', mv.case_delete, name='case_delete'),
    path('case/update/', mv.case_update, name='case_update'),

    path('steps/', mv.steps, name='steps'),
    path('step/<int:object_id>/', mv.step, name='step'),
    path('step/add/', mv.step_add, name='step_add'),
    path('step/delete/', mv.step_delete, name='step_delete'),
    path('step/update/', mv.step_update, name='step_update'),

    path('action_list/', mv.action_list, name='action_list'),
    path('test/', mv.test, name='test'),
    path('logout/', mv.logout, name='logout'),

]

