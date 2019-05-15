from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from .models import Expense, ExpenseName, ExpenseSubName


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
        widgets = {
            'date': DatePickerInput(format='%Y-%m-%d'),
            'price': forms.TextInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class ExpenseSubNameForm(forms.ModelForm):
    class Meta:
        model = ExpenseSubName
        fields = '__all__'

    fields_order = ['parent', 'title']
