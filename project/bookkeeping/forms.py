from crispy_forms.helper import FormHelper
from django import forms
from django.forms.models import modelformset_factory

from ..core.helpers.helper_forms import set_field_properties
from .models import SavingType, SavingWorth


class SavingWorthForm(forms.ModelForm):
    class Meta:
        model = SavingWorth
        fields = ['saving_type', 'price']

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
