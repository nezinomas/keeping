from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import ChainedDropDown, set_field_properties
from .models import Income


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['date', 'account', 'amount', 'remark']

        widgets = {
            'date': DatePickerInput(format='%Y-%m-%d'),
        }

    field_order = ['date', 'account', 'amount', 'remark']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['amount'].widget.attrs = {'step': '0.01'}
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['date'].initial = datetime.now()
        self.fields['amount'].initial = '0.01'

        self.fields['date'].label = 'Data'
        self.fields['account'].label = 'Sąskaita'
        self.fields['amount'].label = 'Suma'
        self.fields['remark'].label = 'Pastaba'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
