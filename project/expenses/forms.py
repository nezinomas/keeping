from django import forms

from crispy_forms.helper import FormHelper

from .models import Expense, ExpenseName, ExpenseSubName


class ExpenseSubNameForm(forms.ModelForm):
    class Meta:
        model = ExpenseSubName
        fields = '__all__'

    fields_order = ['parent', 'title']
