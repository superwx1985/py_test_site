from django.contrib import admin
from .models import *
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin


class MyAdmin(admin.AdminSite):
    site_header = '{}后台'.format(settings.SITE_NAME)


# 使用默认后台
# admin_site = admin.site


# 使用自定义后台
admin_site = MyAdmin()


# 保存时自动保存当前用户到创建者和修改者字段
# def save_model_(request, obj, change):
#     if not change:
#         obj.creator = request.user
#         obj.modifier = request.user
#     else:
#         obj.modifier = request.user
#     obj.save()


class CaseAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'project', 'variable_group', 'creator', 'created_date', 'modifier', 'modified_date',
        'is_active',)
    list_display_links = ('pk', 'name')
    list_filter = ('is_active', 'creator', 'project', 'created_date',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)

    # 其中obj是修改后的对象，form是返回的表单（修改后的），当新建一个对象时change=False, 当修改一个对象时change=True
    # def save_model(self, request, obj, form, change):
    #     save_model_(request, obj, change)


class ActionAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'code', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active', 'type',
        'order')
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'type', 'created_date',)
    list_editable = ('is_active', 'order',)
    search_fields = ('pk', 'name', 'keyword',)


class StepAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'project', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',
        'action',)
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'project', 'created_date',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword', 'action__name',)


class ActionTypeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'is_active',)
    list_display_links = ('pk', 'name',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name',)


class ConfigAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',)
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'created_date',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class CaseVsStepAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'case_id', 'case', 'step_id', 'step', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',
        'order')
    list_display_links = ('pk', 'case', 'step')
    list_filter = ('is_active', 'case', 'step', 'created_date',)
    list_editable = ('is_active',)
    search_fields = ('pk',)


class VariableGroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',)
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'project', 'created_date',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class VariableAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'value', 'order', 'variable_group')
    list_display_links = ('pk', 'name',)
    list_filter = ('variable_group',)
    search_fields = ('pk', 'name',)


class ElementGroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',)
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'project', 'created_date',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class ElementAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'by', 'locator', 'order', 'element_group')
    list_display_links = ('pk', 'name',)
    list_filter = ('element_group',)
    search_fields = ('pk', 'name',)


class SuiteAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'variable_group', 'config', 'keyword', 'creator', 'created_date', 'modifier',
        'modified_date', 'is_active',)
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'project', 'created_date',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class SuiteVsCaseAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'suite_id', 'suite', 'case_id', 'case', 'creator', 'created_date', 'modifier', 'modified_date',
        'is_active', 'order')
    list_display_links = ('pk', 'suite', 'case', 'created_date',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class SuiteResultAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date',
        'start_date', 'end_date', 'execute_count', 'pass_count', 'fail_count', 'error_count', 'is_active')
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'project', 'created_date',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword')


class ImageAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'img')
    list_display_links = ('pk', 'name',)
    search_fields = ('pk', 'name',)


class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'order')
    list_display_links = ('pk', 'name',)
    list_editable = ('order',)
    search_fields = ('pk', 'name', 'keyword',)


class TokenAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'value', 'expire_date', 'user', 'is_active')
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'user')
    list_editable = ('value', 'expire_date', 'user', 'is_active',)
    search_fields = ('pk', 'name', 'keyword', 'value')


admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)

admin_site.register(Case, CaseAdmin)
admin_site.register(Action, ActionAdmin)
admin_site.register(Step, StepAdmin)
admin_site.register(ActionType, ActionTypeAdmin)
admin_site.register(Config, ConfigAdmin)
admin_site.register(CaseVsStep, CaseVsStepAdmin)
admin_site.register(VariableGroup, VariableGroupAdmin)
admin_site.register(Variable, VariableAdmin)
admin_site.register(ElementGroup, ElementGroupAdmin)
admin_site.register(Element, ElementAdmin)
admin_site.register(Suite, SuiteAdmin)
admin_site.register(SuiteVsCase, SuiteVsCaseAdmin)
admin_site.register(SuiteResult, SuiteResultAdmin)
admin_site.register(Image, ImageAdmin)
admin_site.register(Project, ProjectAdmin)
admin_site.register(Token, TokenAdmin)
