from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..accounts.models import Account
from ..core.helpers.helper_forms import ChainedDropDown, set_field_properties
from ..core.lib.date import set_year_for_form
from .models import SavingChange, SavingClose, SavingType, Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'from_account', 'to_account', 'price']

        widgets = {
            'date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['date', 'from_account', 'to_account', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # initial values
        self.fields['price'].initial = '0.01'
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['price'].label = 'Suma'
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['from_account'].queryset = Account.objects.items()
        self.fields['to_account'].queryset = Account.objects.items()

        # field labels
        self.fields['date'].label = 'Data'
        self.fields['from_account'].label = 'Iš sąskaitos'
        self.fields['to_account'].label = 'Į sąskaitą'

        # chained dropdown
        _id = ChainedDropDown(self, 'from_account').parent_field_id
        if _id:
            self.fields['to_account'].queryset = (
                Account.objects.items().exclude(pk=_id)
            )

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class SavingCloseForm(forms.ModelForm):
    class Meta:
        model = SavingClose
        fields = ['date', 'from_account', 'to_account', 'price', 'fee']

        widgets = {
            'date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['date', 'from_account', 'to_account', 'price', 'fee']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form input settings
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['fee'].widget.attrs = {'step': '0.01'}

        # form initial values
        self.fields['date'].initial = set_year_for_form()
        self.fields['price'].initial = '0.01'
        self.fields['fee'].initial = '0.00'

        # overwrite ForeignKey expense_type queryset
        self.fields['from_account'].queryset = SavingType.objects.items()
        self.fields['to_account'].queryset = Account.objects.items()

        # form fields labels
        self.fields['price'].label = 'Suma'
        self.fields['price'].help_text = 'Suma kuri lieka atskaičius mokesčius'
        self.fields['fee'].label = 'Mokesčiai'
        self.fields['date'].label = 'Data'
        self.fields['from_account'].label = 'Iš sąskaitos'
        self.fields['to_account'].label = 'Į sąskaitą'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class SavingChangeForm(forms.ModelForm):
    class Meta:
        model = SavingChange
        fields = ['date', 'from_account', 'to_account', 'price', 'fee']

        widgets = {
            'date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['date', 'from_account', 'to_account', 'price', 'fee']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form input settings
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['fee'].widget.attrs = {'step': '0.01'}

        # initial values
        self.fields['date'].initial = set_year_for_form()
        self.fields['price'].initial = '0.01'
        self.fields['fee'].initial = '0.00'

        # overwrite ForeignKey expense_type queryset
        self.fields['from_account'].queryset = SavingType.objects.items()
        self.fields['to_account'].queryset = SavingType.objects.items()

        # fields labels
        self.fields['price'].label = 'Suma'
        self.fields['price'].help_text = 'Suma kuri lieka atskaičius mokesčius'
        self.fields['fee'].label = 'Mokesčiai'
        self.fields['date'].label = 'Data'
        self.fields['from_account'].label = 'Iš sąskaitos'
        self.fields['to_account'].label = 'Į sąskaitą'

        # chained dropdown
        _id = ChainedDropDown(self, 'from_account').parent_field_id
        if _id:
            self.fields['to_account'].queryset = (
                SavingType.objects.exclude(pk=_id)
            )

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
