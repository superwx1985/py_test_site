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
        'id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',)
    list_display_links = ('id', 'name',)
    list_filter = ('creator',)

    # 其中obj是修改后的对象，form是返回的表单（修改后的），当新建一个对象时change=False, 当修改一个对象时change=True
    # def save_model(self, request, obj, form, change):
    #     save_model_(request, obj, change)


class ActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active', 'type')
    list_display_links = ('id', 'name',)
    list_filter = ('type',)


class StepAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active', 'action',)
    list_display_links = ('id', 'name',)
    list_filter = ('action',)


class ActionTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active',)
    list_display_links = ('id', 'name',)


class ConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',)
    list_display_links = ('id', 'name',)


class CaseVsStepAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'case_id', 'case', 'step_id', 'step', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',
        'order')
    list_display_links = ('id', 'case', 'step')


class VariableGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',)
    list_display_links = ('id', 'name',)


class VariableAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'value', 'order',)
    list_display_links = ('id', 'name',)


class SuiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',)
    list_display_links = ('id', 'name',)


class SuiteVsCaseAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'suite_id', 'suite', 'case_id', 'case', 'creator', 'created_date', 'modifier', 'modified_date', 'is_active',
        'order')
    list_display_links = ('id', 'suite', 'case')


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
