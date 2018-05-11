from django import forms


class StepForm(forms.Form):
    name = forms.CharField(max_length=10, widget=forms.Textarea(attrs={'rows': ''}))
    description = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    keyword = forms.CharField(max_length=100, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    action = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'rows': '', 'style': "display: none"}))
    # action = forms.ChoiceField()
    timeout = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    save_as = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={'rows': ''}))
    ui_by = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'rows': ''}))

