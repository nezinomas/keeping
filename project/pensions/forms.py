from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from .models import Pension, PensionType


class PensionForm(forms.ModelForm):
    class Meta:
        model = Pension
        fields = ['date', 'price', 'remark', 'pension_type']

        widgets = {
            'date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['date', 'pension_type', 'price', 'remark']

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['date'].initial = datetime.now()
        self.fields['pension_type'].initial = 1

        self.fields['date'].label = 'Data'
        self.fields['price'].label = 'Suma'
        self.fields['remark'].label = 'Pastaba'
        self.fields['pension_type'].label = 'Fondas'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class PensionTypeForm(forms.ModelForm):
    class Meta:
        model = PensionType
        fields = ['title']

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].label = 'Fondo pavadinimas'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
