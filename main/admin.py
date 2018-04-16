from django.contrib import admin
from .models import ActionType, Config, Group, Case, Action, Step, CaseVsStep


def save_model_(request, obj, change):
    if not change:
        obj.creator = request.user
        obj.modifier = request.user
    else:
        obj.modifier = request.user
    obj.save()


class CaseAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_valid', 'config',)
    list_display_links = ('id', 'name',)
    list_filter = ('config',)

    # 其中obj是修改后的对象，form是返回的表单（修改后的），当新建一个对象时change=False, 当修改一个对象时change=True
    # def save_model(self, request, obj, form, change):
    #     save_model_(request, obj, change)


class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_valid',)
    list_display_links = ('id', 'name',)


class ActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_valid', 'type')
    list_display_links = ('id', 'name',)
    list_filter = ('type',)


class StepAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_valid', 'action',)
    list_display_links = ('id', 'name',)
    list_filter = ('action',)


class ActionTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_valid',)
    list_display_links = ('id', 'name',)


class ConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'keyword', 'creator', 'created_date', 'modifier', 'modified_date', 'is_valid',)
    list_display_links = ('id', 'name',)


class CaseVsStepAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'case_id', 'case', 'step_id', 'step', 'creator', 'created_date', 'modifier', 'modified_date', 'is_valid',
        'order')
    list_display_links = ('id', 'case', 'step')


admin.site.register(Group, GroupAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(Step, StepAdmin)
admin.site.register(ActionType, ActionTypeAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(CaseVsStep, CaseVsStepAdmin)
