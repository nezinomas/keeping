from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties, ChainedDropDown
from .models import Transaction
from ..accounts.models import Account


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'from_account', 'to_account', 'amount']

        widgets = {
            'date': DatePickerInput(format='%Y-%m-%d'),
        }

    field_order = ['date', 'from_account', 'to_account', 'amount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['amount'].widget.attrs = {'step': '0.01'}

        # inital values
        self.fields['date'].initial = datetime.now()
        self.fields['amount'].initial = '0.01'

        self.fields['date'].label = 'Data'
        self.fields['from_account'].label = 'Iš sąskaitos'
        self.fields['to_account'].label = 'Į sąskaitą'
        self.fields['amount'].label = 'Suma'

        # chained dropdown
        id = ChainedDropDown(self, 'from_account').parent_field_id
        if id:
            self.fields['to_account'].queryset = (
                Account.objects.exclude(pk=id)
            )

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
