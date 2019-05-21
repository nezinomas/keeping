from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from .models import Expense, ExpenseType, ExpenseName


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
        widgets = {
            'date': DatePickerInput(format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['price'].widget.attrs = {'readonly': True, 'step': '0.01'}
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['date'].initial = datetime.now()
        self.fields['account'].initial = 1
        self.fields['price'].initial = '0.00'
        self.fields['expense_name'].queryset = Expense.objects.none()

        if 'expense_type' in self.data:
            try:
                expense_type_id = int(self.data.get('expense_type'))
                self.fields['expense_name'].queryset = (
                    ExpenseName.objects.
                    filter(parent_id=expense_type_id).
                    order_by('title')
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['expense_name'].queryset = (
                self.instance.expense_type.expensename_set.
                order_by('title')
            )

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class ExpenseNameForm(forms.ModelForm):
    class Meta:
        model = ExpenseName
        fields = '__all__'

    fields_order = ['parent', 'title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
