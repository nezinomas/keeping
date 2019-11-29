from datetime import datetime

from bootstrap_datepicker_plus import YearPickerInput
from crispy_forms.helper import FormHelper
from dateutil.relativedelta import relativedelta
from django import forms
from django.apps import apps
from django.core.validators import MaxValueValidator, MinValueValidator

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib.date import monthnames, set_year_for_form
from ..core.lib import utils
from ..core.mixins.form_mixin import FormMixin
from ..expenses.models import ExpenseType
from ..incomes.models import IncomeType
from ..savings.models import SavingType
from .models import (DayPlan, ExpensePlan, IncomePlan, NecessaryPlan,
                     SavingPlan, SavingType)


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


# ----------------------------------------------------------------------------
#                                                             Income Plan Form
# ----------------------------------------------------------------------------
class IncomePlanForm(FormMixin, forms.ModelForm):
    class Meta:
        model = IncomePlan
        fields = ['year', 'income_type'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'income_type'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['income_type'].queryset = IncomeType.objects.items()

        # field translation
        self.fields['income_type'].label = 'Išlaidų rūšis'
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        income_type = cleaned_data.get('income_type')

        # if update
        if 'year' not in self.changed_data:
            return

        qs = IncomePlan.objects.year(year).filter(income_type=income_type)
        if qs.exists():
            _msg = f'{year} metai jau turi {income_type} planą.'
            raise forms.ValidationError([{'__all__': _msg}])

        return


# ----------------------------------------------------------------------------
#                                                            Expense Plan Form
# ----------------------------------------------------------------------------
class ExpensePlanForm(FormMixin, forms.ModelForm):
    class Meta:
        model = ExpensePlan
        fields = ['year', 'expense_type'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'expense_type'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['expense_type'].queryset = ExpenseType.objects.items()

        # field translation
        self.fields['expense_type'].label = 'Išlaidų rūšis'
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        expense_type = cleaned_data.get('expense_type')

        # if update
        if 'year' not in self.changed_data:
            return

        qs = ExpensePlan.objects.year(year).filter(expense_type=expense_type)
        if qs.exists():
            _msg = f'{year} metai jau turi {expense_type} planą.'
            raise forms.ValidationError([{'__all__': _msg}])

        return


# ----------------------------------------------------------------------------
#                                                              Saving Plan Form
# ----------------------------------------------------------------------------
class SavingPlanForm(FormMixin, forms.ModelForm):
    class Meta:
        model = SavingPlan
        fields = ['year', 'saving_type'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'saving_type'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # overwrite ForeignKey expense_type queryset
        self.fields['saving_type'].queryset = SavingType.objects.items()

        # inital values
        self.fields['year'].initial = set_year_for_form()

        # field translation
        self.fields['saving_type'].label = 'Taupymo rūšis'
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        saving_type = cleaned_data.get('saving_type')

        # if update
        if 'year' not in self.changed_data:
            return

        qs = SavingPlan.objects.year(year).filter(saving_type=saving_type)
        if qs.exists():
            _msg = f'{year} metai jau turi {saving_type} planą.'
            raise forms.ValidationError([{'__all__': _msg}])

        return


# ----------------------------------------------------------------------------
#                                                                Day Plan Form
# ----------------------------------------------------------------------------
class DayPlanForm(FormMixin, forms.ModelForm):
    class Meta:
        model = DayPlan
        fields = ['year'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = set_year_for_form()

        # field translation
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')

        # if update
        if 'year' not in self.changed_data:
            return

        qs = DayPlan.objects.year(year)
        if qs.exists():
            _msg = f'{year} metai jau turi Dienos planą.'
            raise forms.ValidationError([{'__all__': _msg}])

        return


# ----------------------------------------------------------------------------
#                                                          Necessary Plan Form
# ----------------------------------------------------------------------------
class NecessaryPlanForm(FormMixin, forms.ModelForm):
    class Meta:
        model = NecessaryPlan
        fields = ['year', 'title'] + monthnames()

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'title'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = set_year_for_form()

        # field translation
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        title = cleaned_data.get('title')

        # if update
        if 'year' not in self.changed_data:
            return

        qs = NecessaryPlan.objects.year(year).filter(title=title)
        if qs.exists():
            _msg = f'{year} metai jau turi {title} planą.'
            raise forms.ValidationError([{'__all__': _msg}])

        return


# ----------------------------------------------------------------------------
#                                                               Copy Plan Form
# ----------------------------------------------------------------------------
class CopyPlanForm(forms.Form):
    year_from = forms.IntegerField(
        widget=YearPickerInput(format='%Y'),
        validators=[
            MinValueValidator(1974),
            MaxValueValidator(2050)],
    )
    year_to = forms.IntegerField(
        widget=YearPickerInput(format='%Y'),
        validators=[
            MinValueValidator(1974),
            MaxValueValidator(2050)],
    )
    income = forms.BooleanField(required=False)
    expense = forms.BooleanField(required=False)
    saving = forms.BooleanField(required=False)
    day = forms.BooleanField(required=False)
    necessary = forms.BooleanField(required=False)

    def _get_cleaned_checkboxes(self, cleaned_data):
        dict_ = {
            'income': cleaned_data.get("income"),
            'expense': cleaned_data.get("expense"),
            'saving': cleaned_data.get("saving"),
            'day': cleaned_data.get("day"),
            'necessary': cleaned_data.get("necessary"),
        }
        return dict_

    def _get_model(self, name):
        return apps.get_model(f'plans.{name.title()}Plan')

    def _append_error_message(self, msg, errors, key):
        err = errors.get(key)
        if err:
            err.append(msg)
            errors[key] = err
        else:
            errors[key] = [msg]

    def clean(self):
        cleaned_data = super().clean()

        dict_ = self._get_cleaned_checkboxes(cleaned_data)
        year_from = cleaned_data.get('year_from')
        year_to = cleaned_data.get('year_to')

        # at least one checkbox must be selected
        chk = [v for k, v in dict_.items() if v]

        if not chk:
            raise forms.ValidationError(
                "Reikia pažymėti nors vieną planą."
            )

        # copy from table must contain data
        errors = {}
        msg = 'Nėra ką kopijuoti.'
        for k, v in dict_.items():
            if v:
                model = self._get_model(k)
                qs = model.objects.year(year_from)
                if not qs.exists():
                    self._append_error_message(msg, errors, k)

        # copy to table must be empty
        msg = f'{year_to} metai jau turi planus.'
        for k, v in dict_.items():
            if v:
                model = self._get_model(k)
                qs = model.objects.year(year_to)
                if qs.exists():
                    self._append_error_message(msg, errors, k)

        if errors:
            raise forms.ValidationError(errors)

    def save(self):
        dict_ = self._get_cleaned_checkboxes(self.cleaned_data)
        year_from = self.cleaned_data.get('year_from')
        year_to = self.cleaned_data.get('year_to')

        for k, v in dict_.items():
            if v:
                model = self._get_model(k)
                qs = model.objects.year(year_from).values_list('pk', flat=True)

                for i in qs:
                    obj = model.objects.get(pk=i)
                    obj.pk = None
                    obj.year = year_to
                    obj.save()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # initail values
        self.fields['year_from'].initial = datetime.now()
        self.fields['year_to'].initial = datetime.now() + relativedelta(years=1)
        self.fields['income'].initial = True
        self.fields['expense'].initial = True
        self.fields['saving'].initial = True
        self.fields['day'].initial = True
        self.fields['necessary'].initial = True

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
