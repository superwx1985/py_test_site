from django import forms
from .models import Action, Step
from django.contrib.admin.widgets import FilteredSelectMultiple


class StepForm(forms.Form):
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

    class Meta:
        model = Step
        fields = ['name', 'action']


