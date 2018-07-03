from django.contrib import admin
from .models import *

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
    list_filter = ('is_active', 'creator', 'project')
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)

    # 其中obj是修改后的对象，form是返回的表单（修改后的），当新建一个对象时change=False, 当修改一个对象时change=True
    # def save_model(self, request, obj, form, change):
    #     save_model_(request, obj, change)


class ActionAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active', 'type', 'order')
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'type',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class StepAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'project', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active', 'action',)
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'project')
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class ActionTypeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'is_active',)
    list_display_links = ('pk', 'name',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name',)


class ConfigAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',)
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator')
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class CaseVsStepAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'case_id', 'case', 'step_id', 'step', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',
        'order')
    list_display_links = ('pk', 'case', 'step')
    list_filter = ('is_active', 'case', 'step')
    list_editable = ('is_active',)
    search_fields = ('pk',)


class VariableGroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'project', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',)
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'project')
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class VariableAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'value', 'order', 'variable_group')
    list_display_links = ('pk', 'name',)
    list_filter = ('variable_group',)
    search_fields = ('pk', 'name',)


class SuiteAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'variable_group', 'config', 'keyword', 'creator', 'created_date', 'modifier',
        'modified_date', 'is_active',)
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'project')
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class SuiteVsCaseAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'suite_id', 'suite', 'case_id', 'case', 'creator', 'created_date', 'modifier', 'modified_date',
        'is_active', 'order')
    list_display_links = ('pk', 'suite', 'case',)
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class SuiteResultAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'project', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date',
        'start_date', 'end_date', 'execute_count', 'pass_count', 'fail_count', 'error_count', 'is_active')
    list_display_links = ('pk', 'name',)
    list_filter = ('is_active', 'creator', 'project')
    list_editable = ('is_active',)
    search_fields = ('pk', 'name', 'keyword',)


class ImageAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'img')
    list_display_links = ('pk', 'name',)
    search_fields = ('pk', 'name',)


class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'keyword', 'order')
    list_display_links = ('pk', 'name',)
    search_fields = ('pk', 'name', 'keyword',)


admin.site.register(Case, CaseAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(Step, StepAdmin)
admin.site.register(ActionType, ActionTypeAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(CaseVsStep, CaseVsStepAdmin)
admin.site.register(VariableGroup, VariableGroupAdmin)
admin.site.register(Variable, VariableAdmin)
admin.site.register(Suite, SuiteAdmin)
admin.site.register(SuiteVsCase, SuiteVsCaseAdmin)
admin.site.register(SuiteResult, SuiteResultAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Project, ProjectAdmin)
