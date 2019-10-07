from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..accounts.models import Account
from ..core.helpers.helper_forms import ChainedDropDown, set_field_properties
from .models import Expense, ExpenseName, ExpenseType


class ExpenseForm(forms.ModelForm):
    total_sum = forms.CharField(required=False)

    class Meta:
        model = Expense
        fields = ('date', 'price', 'quantity', 'expense_type',
                  'expense_name', 'remark', 'exception', 'account')
        widgets = {
            'date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['date', 'expense_type', 'expense_name', 'account',
                   'total_sum', 'quantity', 'remark', 'price', 'exception']

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # field translation
        self.fields['date'].label = 'Data'
        self.fields['price'].label = 'Visa kaina'
        self.fields['quantity'].label = 'Kiekis'
        self.fields['expense_type'].label = 'Išlaidų rūšis'
        self.fields['expense_name'].label = 'Išlaidų pavadinimas'
        self.fields['remark'].label = 'Pastaba'
        self.fields['exception'].label = 'Nenaudoti planuose'
        self.fields['account'].label = 'Sąskaita'
        self.fields['total_sum'].label = 'Kaina'

        # form inputs settings
        self.fields['price'].widget.attrs = {'readonly': True, 'step': '0.01'}
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['date'].initial = datetime.now()
        self.fields['account'].initial = Account.objects.first()
        self.fields['price'].initial = '0.00'
        self.fields['expense_name'].queryset = Expense.objects.none()

        # chained dropdown
        id = ChainedDropDown(self, 'expense_type').parent_field_id
        if id:
            if not year:
                year = datetime.now().year

            self.fields['expense_name'].queryset = (
                ExpenseName.objects.parent(id).year(year)
            )

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = '__all__'

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['title'].label = 'Pavadinimas'
        self.fields['necessary'].label = 'Būtina'


class ExpenseNameForm(forms.ModelForm):
    class Meta:
        model = ExpenseName
        fields = ['parent', 'title', 'valid_for']

        widgets = {
            'valid_for': YearPickerInput(format='%Y'),
        }

    field_order = ['parent', 'title', 'valid_for']

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['parent'].label = 'Išlaidų rūšis'
        self.fields['title'].label = 'Išlaidų pavadinimas'
        self.fields['valid_for'].label = 'Galioja tik'
