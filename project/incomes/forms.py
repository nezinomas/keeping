from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from .models import Income, IncomeType


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['date', 'price', 'remark', 'account', 'income_type']

        widgets = {
            'date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['date', 'income_type', 'account', 'price', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['account'].initial = Account.objects.items().first()
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['income_type'].queryset = IncomeType.objects.items()
        self.fields['account'].queryset = Account.objects.items()

        self.fields['date'].label = 'Data'
        self.fields['account'].label = 'Sąskaita'
        self.fields['price'].label = 'Suma'
        self.fields['remark'].label = 'Pastaba'
        self.fields['income_type'].label = 'Pajamų rūšis'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class IncomeTypeForm(forms.ModelForm):
    class Meta:
        model = IncomeType
        fields = ['journal', 'title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # user input
        self.fields['journal'].initial = utils.get_journal()
        self.fields['journal'].disabled = True
        self.fields['journal'].widget = forms.HiddenInput()

        self.fields['title'].label = 'Pajamų rūšis'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
