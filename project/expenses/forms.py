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

        self.fields['sub_category'].queryset = Expense.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['sub_category'].queryset = (
                    ExpenseSubName.objects.
                    filter(parent_id=category_id).
                    order_by('title')
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['sub_category'].queryset = (
                self.instance.category.sub_category_set.
                order_by('title')
            )

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class ExpenseSubNameForm(forms.ModelForm):
    class Meta:
        model = ExpenseSubName
        fields = '__all__'

    fields_order = ['parent', 'title']
