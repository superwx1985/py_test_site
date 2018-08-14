from django import forms
from main.models import *
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _


class StepForm0(forms.Form):
    name = forms.CharField(max_length=10, widget=forms.Textarea(attrs={'rows': ''}))
    description = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    keyword = forms.CharField(max_length=100, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    # action = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'rows': '', 'style': "display: none"}))
    # action = forms.models.ModelChoiceField(queryset=Action.objects.all())
    action = forms.ModelChoiceField(queryset=Action.objects)
    # action = forms.ModelMultipleChoiceField(Action.objects)
    timeout = forms.FloatField(min_value=0, required=False, max_value=9999)
    save_as = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    ui_by = forms.ChoiceField(choices=Step.ui_by_list, required=False)
    ui_locator = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    ui_index = forms.IntegerField(min_value=0, required=False)
    ui_base_element = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    ui_data = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    ui_special_action = forms.ChoiceField(choices=Step.ui_special_action_list, required=False)
    ui_alert_handle = forms.ChoiceField(choices=Step.ui_alert_handle_list, required=False, widget=forms.RadioSelect)
    api_url = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    api_headers = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    api_body = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    api_data = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))


class LoginForm(forms.Form):
    username = forms.CharField(label='用户名', max_length=50)
    password = forms.CharField(label='密码', max_length=50, widget=forms.PasswordInput())
    remember_me = forms.BooleanField(label='记住我', required=False)


class UserForm(forms.Form):
    last_name = forms.CharField(label='姓', max_length=50, required=False)
    first_name = forms.CharField(label='名', max_length=50, required=False)
    original_password = forms.CharField(
        label='原密码', max_length=50, widget=forms.PasswordInput(), required=False)
    new_password = forms.CharField(
        label='新密码', max_length=50, required=False, strip=False)
    confirm_password = forms.CharField(
        label='确认密码', max_length=50, required=False, strip=False)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    # def clean(self):
    #     new_password = self.cleaned_data.get('new_password')
    #     if new_password and self.cleaned_data['new_password'] != self.cleaned_data['confirm_password']:
    #         raise forms.ValidationError(_("The two password fields didn't match."))
    #         # raise forms.ValidationError('两次输入的密码不一致')
    #     else:
    #         cleaned_data = super(UserForm, self).clean()
    #     return cleaned_data

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            password_validation.validate_password(new_password, self.user)
        return new_password

    def clean_confirm_password(self):
        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if new_password and new_password != confirm_password:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return confirm_password


class PaginatorForm(forms.Form):
    # page = forms.IntegerField(min_value=1, required=False)
    size = forms.IntegerField(min_value=1, max_value=10000, required=False)

    def __init__(self, page_max_value, *args, **kwargs):
        super(PaginatorForm, self).__init__(*args, **kwargs)

        self.fields['page'] = forms.IntegerField(min_value=1, max_value=page_max_value, required=False)

        # for k, v in self.fields.items():
        #     v.widget.attrs.update({'class': 'form-control', 'style': 'width: 85px'})


class OrderByForm(forms.Form):
    order_by = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput)
    order_by_reverse = forms.BooleanField(required=False, widget=forms.HiddenInput)


class CaseForm(forms.ModelForm):
    # 不验证某些字段
    is_active = forms.CharField(required=False, validators=[])
    step = forms.CharField(required=False, validators=[])
    # 限制project为必选
    project = forms.ModelChoiceField(queryset=Project.objects, required=True)

    class Meta:
        model = Case
        fields = '__all__'
        widgets = {
            # 'name': forms.Textarea(),
            # 'keyword': forms.Textarea(),
            # 'save_as': forms.Textarea(),
            # 'ui_alert_handle': forms.RadioSelect,
        }

    # def __init__(self, *args, **kwargs):
    #     super(CaseForm, self).__init__(*args, **kwargs)
    #
    #     for k, v in self.fields.items():
    #         if k == 'name':
    #             v.widget.attrs.update({'placeholder': '请输入名称'})
    #         # 如果widget是Textarea，rows属性设置为空
    #         if isinstance(v.widget, forms.Textarea):
    #             v.widget.attrs.update({'rows': '', 'class': 'form-control'})
    #         else:
    #             v.widget.attrs.update({'class': 'form-control'})


class StepForm(forms.ModelForm):
    # 优化查询数量，防止对action type查询多次
    action = forms.ModelChoiceField(
        queryset=Action.objects.select_related('creator', 'modifier', 'type'))
    # 排序子用例
    other_sub_case = forms.ModelChoiceField(queryset=Case.objects.filter(is_active=True).order_by('pk'), required=False)
    # 不验证某些字段
    is_active = forms.CharField(required=False, validators=[])
    # 限制project为必选
    project = forms.ModelChoiceField(queryset=Project.objects, required=True)
    # 限制timeout大于1
    timeout = forms.FloatField(min_value=1, required=False)

    class Meta:
        model = Step
        fields = '__all__'
        widgets = {
            # 'name': forms.Textarea(),
            # 'keyword': forms.Textarea(),
            # 'save_as': forms.Textarea(),
            # 'ui_alert_handle': forms.RadioSelect,
        }

    # def __init__(self, *args, **kwargs):
    #     super(StepForm, self).__init__(*args, **kwargs)
    #
    #     for k, v in self.fields.items():
    #         # 如果widget是Textarea，rows属性设置为空
    #         if isinstance(v.widget, forms.Textarea):
    #             v.widget.attrs.update({'rows': '', 'class': 'form-control'})
    #         else:
    #             v.widget.attrs.update({'class': 'form-control'})


class ConfigForm(forms.ModelForm):
    # 不验证某些字段
    is_active = forms.CharField(required=False, validators=[])

    class Meta:
        model = Config
        fields = '__all__'


class VariableGroupForm(forms.ModelForm):
    # 不验证某些字段
    is_active = forms.CharField(required=False, validators=[])
    # 限制project为必选
    project = forms.ModelChoiceField(queryset=Project.objects, required=True)

    class Meta:
        model = VariableGroup
        fields = '__all__'


# class VariableForm(forms.ModelForm):
#     # 不验证某些字段
#     creator = forms.ModelChoiceField(queryset=User.objects, required=False, validators=[])
#     modifier = forms.ModelChoiceField(queryset=User.objects, required=False, validators=[])
#     is_active = forms.CharField(required=False, validators=[])
#
#     class Meta:
#         model = Variable
#         fields = '__all__'


class SuiteForm(forms.ModelForm):
    # 不验证某些字段
    is_active = forms.CharField(required=False, validators=[])
    case = forms.CharField(required=False, validators=[])
    # 限制线程数最大值
    thread_count = forms.IntegerField(initial=1, min_value=1, max_value=8)
    # 限制config为必选
    config = forms.ModelChoiceField(queryset=Config.objects, required=True)
    # 限制project为必选
    project = forms.ModelChoiceField(queryset=Project.objects, required=True)
    # 限制timeout大于1
    timeout = forms.FloatField(min_value=1)

    class Meta:
        model = Suite
        fields = '__all__'


# 动态获取project
def get_project_list():
    project_list = list()
    project_list.append((None, '---------'))
    project_list.extend(list(Project.objects.values_list('pk', 'name')))
    return project_list


class SuiteResultForm(forms.Form):
    name = forms.CharField(max_length=100)
    description = forms.CharField(required=False, widget=forms.Textarea())
    keyword = forms.CharField(required=False, max_length=100)
    project = forms.ChoiceField(choices=get_project_list, required=False)
