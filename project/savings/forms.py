from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from .models import Saving, SavingType


class SavingTypeForm(forms.ModelForm):
    class Meta:
        model = SavingType
        fields = ['title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].label = 'Fondas'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class SavingForm(forms.ModelForm):
    class Meta:
        model = Saving
        fields = ['date', 'amount', 'fee', 'remark', 'saving_type', 'account']

        widgets = {
            'date': DatePickerInput(format='%Y-%m-%d'),
        }

    field_order = ['date', 'saving_type', 'account', 'amount', 'fee', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['amount'].widget.attrs = {'step': '0.01'}
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['date'].initial = datetime.now()
        self.fields['amount'].initial = '0.01'

        self.fields['date'].label = 'Data'
        self.fields['account'].label = 'Iš sąskaitos'
        self.fields['amount'].label = 'Suma'
        self.fields['fee'].label = 'Mokesčiai'
        self.fields['remark'].label = 'Pastaba'
        self.fields['saving_type'].label = 'Fondas'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
