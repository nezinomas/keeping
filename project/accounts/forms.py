from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['title']

    def __init__(self, extra={}, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['title'].label = 'Sąskaitos pavadinimas'
