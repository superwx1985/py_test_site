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
from django.contrib import admin
import main.views as mvs

urlpatterns = [
    url('^admin/', admin.site.urls),
    url('^run/$', mvs.run, name='run'),
    url('^list_case/$', mvs.list_case, name='list_case'),
    # url('^tc_list/delete/$', mvs.tc_del, name='tc_del'),
    url('^case/delete/$', mvs.delete_case, name='delete_case'),
    # url('^case/del/$', mvs.tc_del, name='tc_del'),
    url('^case/update/$', mvs.update_case, name='update_case'),
    url('^tc_list/get_tc_list/$', mvs.get_tc_list, name='tc_get_tc_list'),
    url('^tc_list/tc_pagination/$', mvs.tc_pagination, name='tc_pagination'),
]
