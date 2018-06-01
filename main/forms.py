from django import forms
from .models import Action, Step, Case
from django.contrib.auth.models import User
from django.contrib.admin.widgets import FilteredSelectMultiple


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


class PaginatorForm(forms.Form):
    # page = forms.IntegerField(min_value=1, required=False)
    size = forms.IntegerField(min_value=1, max_value=10000, required=False)

    def __init__(self, page_max_value, *args, **kwargs):
        super(PaginatorForm, self).__init__(*args, **kwargs)

        self.fields['page'] = forms.IntegerField(min_value=1, max_value=page_max_value, required=False)

        for k, v in self.fields.items():
            v.widget.attrs.update({'class': 'form-control', 'style': 'width: 85px'})


class CaseForm(forms.ModelForm):
    # 不验证某些字段
    creator = forms.ModelChoiceField(queryset=User.objects, required=False, validators=[])
    modifier = forms.ModelChoiceField(queryset=User.objects, required=False, validators=[])
    is_active = forms.CharField(required=False)

    class Meta:
        model = Case
        fields = '__all__'
        widgets = {
            # 'name': forms.Textarea(),
            # 'keyword': forms.Textarea(),
            # 'save_as': forms.Textarea(),
            # 'ui_alert_handle': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super(CaseForm, self).__init__(*args, **kwargs)

        for k, v in self.fields.items():
            # 如果widget是Textarea，rows属性设置为空
            if isinstance(v.widget, forms.Textarea):
                v.widget.attrs.update({'rows': '', 'class': 'form-control'})
            else:
                v.widget.attrs.update({'class': 'form-control'})


class StepForm(forms.ModelForm):
    # 优化查询数量，防止对action type查询多次
    action = forms.ModelChoiceField(queryset=Action.objects.prefetch_related('type'))
    # 不验证某些字段
    creator = forms.ModelChoiceField(queryset=User.objects, required=False, validators=[])
    modifier = forms.ModelChoiceField(queryset=User.objects, required=False, validators=[])
    is_active = forms.CharField(required=False)

    class Meta:
        model = Step
        fields = '__all__'
        widgets = {
            # 'name': forms.Textarea(),
            # 'keyword': forms.Textarea(),
            # 'save_as': forms.Textarea(),
            # 'ui_alert_handle': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super(StepForm, self).__init__(*args, **kwargs)

        for k, v in self.fields.items():
            # 如果widget是Textarea，rows属性设置为空
            if isinstance(v.widget, forms.Textarea):
                v.widget.attrs.update({'rows': '', 'class': 'form-control'})
            else:
                v.widget.attrs.update({'class': 'form-control'})
