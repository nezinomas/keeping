from datetime import datetime

from crispy_forms.helper import FormHelper
from django import forms
from django.forms.models import modelformset_factory

from ..core.helpers.helper_forms import set_field_properties
from .models import SavingWorth


class SavingWorthForm(forms.ModelForm):
    class Meta:
        model = SavingWorth
        fields = ['price', 'saving_type']

    def __init__(self, extra={}, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

SavingWorthFormset = (
    modelformset_factory(
        SavingWorth,
        exclude=(),
        extra=0,
        form=SavingWorthForm
    )
)
