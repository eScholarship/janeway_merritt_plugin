from django import forms

class MerrittAdminForm(forms.Form):
    merritt_enabled = forms.BooleanField(required=False)
    merritt_collection = forms.CharField(required=False)
    merritt_url = forms.CharField(required=False)


class DummyManagerForm(forms.Form):
    dummy_field = forms.CharField()
