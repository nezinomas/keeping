import calendar
from datetime import datetime

from bootstrap_datepicker_plus import YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib.date import monthnames
from .models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan


def common_field_transalion(self):
    self.fields['year'].label = 'Metai'
    self.fields['january'].label = 'Sausis'
    self.fields['february'].label = 'Vasaris'
    self.fields['march'].label = 'Kovas'
    self.fields['april'].label = 'Balandis'
    self.fields['may'].label = 'Gegužė'
    self.fields['june'].label = 'Birželis'
    self.fields['july'].label = 'Liepa'
    self.fields['august'].label = 'Rugpjūtis'
    self.fields['september'].label = 'Rugsėjis'
    self.fields['october'].label = 'Spalis'
    self.fields['november'].label = 'Lapkritis'
    self.fields['december'].label = 'Gruodis'


class ExpensePlanForm(forms.ModelForm):
    class Meta:
        model = ExpensePlan
        fields = ['year', 'expense_type'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'expense_type'] + monthnames()

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = datetime.now()

        # field translation
        self.fields['expense_type'].label = 'Išlaidų rūšis'
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class IncomePlanForm(forms.ModelForm):
    class Meta:
        model = IncomePlan
        fields = ['year', 'income_type'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'income_type'] + monthnames()

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = datetime.now()

        # field translation
        self.fields['income_type'].label = 'Išlaidų rūšis'
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class SavingPlanForm(forms.ModelForm):
    class Meta:
        model = SavingPlan
        fields = ['year', 'saving_type'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'saving_type'] + monthnames()

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = datetime.now()

        # field translation
        self.fields['saving_type'].label = 'Taupymo rūšis'
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class DayPlanForm(forms.ModelForm):
    class Meta:
        model = DayPlan
        fields = ['year'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year'] + monthnames()

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = datetime.now()

        # field translation
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class NecessaryPlanForm(forms.ModelForm):
    class Meta:
        model = NecessaryPlan
        fields = ['year', 'title'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'title'] + monthnames()

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = datetime.now()

        # field translation
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
