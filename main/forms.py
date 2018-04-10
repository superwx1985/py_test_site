from django import forms

class TcForm(forms.Form):
    name = forms.CharField(max_length=256)
    description = forms.CharField(blank=True)
    keyword = forms.CharField(max_length=256, blank=True, default='')
    order = forms.IntegerField(default=1)