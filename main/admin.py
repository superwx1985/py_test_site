from django.contrib import admin
from .models import *
from django.conf import settings
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin


class MyAdmin(admin.AdminSite):
    site_header = f'{settings.SITE_NAME} Admin'


# 使用默认后台
# admin_site = admin.site
# 使用自定义后台
admin_site = MyAdmin()


class DynPaginationChangeList(ChangeList):
    def __init__(self, request, model, list_display, list_display_links,
                 list_filter, date_hierarchy, search_fields, list_select_related,
                 list_per_page, list_max_show_all, list_editable, model_admin, sortable_by, search_help_text):
        page_param = request.GET.get('list_per_page', None)
        if page_param is not None:
            # Override list_per_page if present in URL
            # Need to be before super call to be applied on filters
            list_per_page = int(page_param)
        super(DynPaginationChangeList, self).__init__(request, model, list_display, list_display_links,
                                                      list_filter, date_hierarchy, search_fields, list_select_related,
                                                      list_per_page, list_max_show_all, list_editable, model_admin,
                                                      sortable_by, search_help_text)

    def get_filters_params(self, params=None):
        """
        Return all params except IGNORED_PARAMS and 'list_per_page'
        """
        lookup_params = super(DynPaginationChangeList, self).get_filters_params(params)
        if 'list_per_page' in lookup_params:
            del lookup_params['list_per_page']
        return lookup_params


class AdminDynPaginationMixin:
    def get_changelist(self, request, **kwargs):
        return DynPaginationChangeList


# 重写 ModelAdmin支持自定义每页条数
class MyModelAdmin(AdminDynPaginationMixin, admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        # Change default number of per page
        page_param = int(request.GET.get('list_per_page', [10])[0])
        # Dynamically set the django admin list size based on query parameter.
        self.list_per_page = page_param
        return super(MyModelAdmin, self).changelist_view(request, extra_context)


@admin.register(Suite, site=admin_site)
class SuiteAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'variable_group', 'config', 'keyword', 'creator', 'created_date', 'modifier',
        'modified_date', 'is_active')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'project', 'creator', 'created_date')
    list_editable = ('is_active', 'creator')
    search_fields = ('pk', 'name', 'keyword')


@admin.register(Case, site=admin_site)
class CaseAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'project', 'variable_group', 'creator', 'created_date', 'modifier', 'modified_date',
        'is_active')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'project', 'creator', 'created_date')
    list_editable = ('is_active', 'creator')
    search_fields = ('pk', 'name', 'keyword')

    # 其中obj是修改后的对象，form是返回的表单（修改后的），当新建一个对象时change=False, 当修改一个对象时change=True
    # def save_model(self, request, obj, form, change):
    #     save_model_(request, obj, change)


@admin.register(SuiteVsCase, site=admin_site)
class SuiteVsCaseAdmin(MyModelAdmin):
    list_display = (
        'pk', 'suite_id', 'suite', 'case_id', 'case', 'creator', 'created_date', 'modifier', 'modified_date',
        'is_active', 'order')
    list_display_links = ('pk', 'suite', 'case', 'created_date')
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword')


@admin.register(Step, site=admin_site)
class StepAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'project', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',
        'action')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'project', 'creator', 'created_date')
    list_editable = ('is_active', 'creator')
    search_fields = ('pk', 'name', 'keyword', 'action__name')


@admin.register(CaseVsStep, site=admin_site)
class CaseVsStepAdmin(MyModelAdmin):
    list_display = (
        'pk', 'case_id', 'case', 'step_id', 'step', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',
        'order')
    list_display_links = ('pk', 'case', 'step')
    list_filter = ('is_active', 'case', 'step', 'created_date')
    list_editable = ('is_active',)
    search_fields = ('pk',)


@admin.register(ActionType, site=admin_site)
class ActionTypeAdmin(MyModelAdmin):
    list_display = ('pk', 'name', 'is_active')
    list_display_links = ('pk', 'name')
    list_editable = ('is_active',)
    search_fields = ('pk', 'name')


@admin.register(Action, site=admin_site)
class ActionAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'code', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active', 'type',
        'order')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'type', 'creator', 'created_date')
    list_editable = ('is_active', 'order')
    search_fields = ('pk', 'name', 'keyword')


@admin.register(Config, site=admin_site)
class ConfigAdmin(MyModelAdmin):
    list_display = ('pk', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'creator', 'created_date')
    list_editable = ('is_active', 'creator')
    search_fields = ('pk', 'name', 'keyword')


@admin.register(VariableGroup, site=admin_site)
class VariableGroupAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'project', 'creator', 'created_date')
    list_editable = ('is_active', 'creator')
    search_fields = ('pk', 'name', 'keyword')


@admin.register(Variable, site=admin_site)
class VariableAdmin(MyModelAdmin):
    list_display = ('pk', 'name', 'value', 'order', 'variable_group')
    list_display_links = ('pk', 'name')
    list_filter = ('variable_group',)
    search_fields = ('pk', 'name')


@admin.register(ElementGroup, site=admin_site)
class ElementGroupAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'project', 'creator', 'created_date')
    list_editable = ('is_active', 'creator')
    search_fields = ('pk', 'name', 'keyword')


@admin.register(Element, site=admin_site)
class ElementAdmin(MyModelAdmin):
    list_display = ('pk', 'name', 'by', 'locator', 'order', 'element_group')
    list_display_links = ('pk', 'name')
    list_filter = ('element_group',)
    search_fields = ('pk', 'name')


@admin.register(SuiteResult, site=admin_site)
class SuiteResultAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date',
        'start_date', 'end_date', 'execute_count', 'pass_count', 'fail_count', 'error_count', 'is_active')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'project', 'creator', 'created_date')
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword')


@admin.register(CaseResult, site=admin_site)
class CaseResultAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'creator',
        'start_date', 'end_date', 'execute_count', 'pass_count', 'fail_count', 'error_count', 'suite_result')
    list_display_links = ('pk', 'name', 'suite_result')
    list_filter = ('creator',)
    search_fields = ('pk', 'name', 'keyword')


@admin.register(StepResult, site=admin_site)
class StepResultAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'creator',
        'start_date', 'end_date', 'result_state', 'case_result')
    list_display_links = ('pk', 'name', 'case_result')
    list_filter = ('creator',)
    search_fields = ('pk', 'name', 'keyword')


@admin.register(Image, site=admin_site)
class ImageAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'img')
    list_display_links = ('pk', 'name')
    search_fields = ('pk', 'name')


@admin.register(Project, site=admin_site)
class ProjectAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'order')
    list_display_links = ('pk', 'name')
    list_editable = ('order',)
    search_fields = ('pk', 'name', 'keyword')


@admin.register(Token, site=admin_site)
class TokenAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'value', 'expire_date', 'user', 'is_active')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'user')
    list_editable = ('value', 'expire_date', 'user', 'is_active')
    search_fields = ('pk', 'name', 'keyword', 'value')


@admin.register(DataSet, site=admin_site)
class DataSetAdmin(MyModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active')
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'project', 'creator', 'created_date')
    list_editable = ('is_active', 'creator')
    search_fields = ('pk', 'name', 'keyword')


admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
