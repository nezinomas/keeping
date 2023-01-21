from datetime import datetime

from bootstrap_datepicker_plus.widgets import YearPickerInput
from crispy_forms.helper import FormHelper
from dateutil.relativedelta import relativedelta
from django import forms
from django.apps import apps
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext as _

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import monthnames, set_year_for_form
from ..core.lib.translation import month_names
from ..expenses.models import ExpenseType
from ..incomes.models import IncomeType
from ..savings.models import SavingType
from .models import (DayPlan, ExpensePlan, IncomePlan, NecessaryPlan,
                     SavingPlan, SavingType)


def common_field_transalion(self):
    self.fields['year'].label = _('Years')

    for key, val in month_names().items():
        self.fields[key.lower()].label = val


def set_journal_field(fields):
    # journal input
    fields['journal'].initial = utils.get_user().journal
    fields['journal'].disabled = True
    fields['journal'].widget = forms.HiddenInput()


class YearCleanMixin:
    def clean(self):
        cleaned_data = super().clean()
        utils.clean_year_picker_input('year', self.data, cleaned_data, self.errors)
        return cleaned_data


# ----------------------------------------------------------------------------
#                                                             Income Plan Form
# ----------------------------------------------------------------------------
class IncomePlanForm(YearCleanMixin, forms.ModelForm):
    class Meta:
        model = IncomePlan
        fields = ['journal', 'year', 'income_type'] + monthnames()

        widgets = {
            'year': YearPickerInput(),
        }

    field_order = ['year', 'income_type'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(self.fields)

        # inital values
        self.fields['year'].initial = set_year_for_form().year

        # overwrite ForeignKey expense_type queryset
        self.fields['income_type'].queryset = IncomeType.objects.items()

        # field translation
        self.fields['income_type'].label = _('Income type')
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


# ----------------------------------------------------------------------------
#                                                            Expense Plan Form
# ----------------------------------------------------------------------------
class ExpensePlanForm(YearCleanMixin, forms.ModelForm):
    class Meta:
        model = ExpensePlan
        fields = ['journal', 'year', 'expense_type'] + monthnames()

        widgets = {
            'year': YearPickerInput(),
        }

    field_order = ['year', 'expense_type'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(self.fields)

        # inital values
        self.fields['year'].initial = set_year_for_form().year

        # overwrite ForeignKey expense_type queryset
        self.fields['expense_type'].queryset = ExpenseType.objects.items()

        # field translation
        self.fields['expense_type'].label = ('Expense type')
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


# ----------------------------------------------------------------------------
#                                                              Saving Plan Form
# ----------------------------------------------------------------------------
class SavingPlanForm(YearCleanMixin, forms.ModelForm):
    class Meta:
        model = SavingPlan
        fields = ['journal', 'year', 'saving_type'] + monthnames()

        widgets = {
            'year': YearPickerInput(),
        }

    field_order = ['year', 'saving_type'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(self.fields)

        # overwrite ForeignKey expense_type queryset
        self.fields['saving_type'].queryset = SavingType.objects.items()

        # inital values
        self.fields['year'].initial = set_year_for_form().year

        # field translation
        self.fields['saving_type'].label = _('Saving type')
        common_field_transalion(self)



        self.helper = FormHelper()
        set_field_properties(self, self.helper)


# ----------------------------------------------------------------------------
#                                                                Day Plan Form
# ----------------------------------------------------------------------------
class DayPlanForm(YearCleanMixin, forms.ModelForm):
    class Meta:
        model = DayPlan
        fields = ['journal', 'year'] + monthnames()

        widgets = {
            'year': YearPickerInput(),
        }

    field_order = ['year'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(self.fields)

        # inital values
        self.fields['year'].initial = set_year_for_form().year

        # field translation
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


# ----------------------------------------------------------------------------
#                                                          Necessary Plan Form
# ----------------------------------------------------------------------------
class NecessaryPlanForm(YearCleanMixin, forms.ModelForm):
    class Meta:
        model = NecessaryPlan
        fields = ['journal', 'year', 'title'] + monthnames()

        widgets = {
            'year': YearPickerInput(),
        }

    field_order = ['year', 'title'] + monthnames()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(self.fields)

        # inital values
        self.fields['year'].initial = set_year_for_form().year

        # field translation
        common_field_transalion(self)

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


# ----------------------------------------------------------------------------
#                                                               Copy Plan Form
# ----------------------------------------------------------------------------
class CopyPlanForm(forms.Form):
    year_from = forms.IntegerField(
        widget=YearPickerInput(),
        validators=[
            MinValueValidator(1974),
            MaxValueValidator(2050)],
    )
    year_to = forms.IntegerField(
        widget=YearPickerInput(),
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

        utils.clean_year_picker_input('year_from', self.data, cleaned_data, self.errors)
        utils.clean_year_picker_input('year_to', self.data, cleaned_data, self.errors)

        year_from = cleaned_data.get('year_from')
        year_to = cleaned_data.get('year_to')

        if not year_to or not year_from:
            return cleaned_data

        # at least one checkbox must be selected
        chk = [v for k, v in dict_.items() if v]

        if not chk:
            raise forms.ValidationError(
                _('At least one plan needs to be selected.')
            )

        # copy from table must contain data
        errors = {}
        msg = _('There is nothing to copy.')
        for k, v in dict_.items():
            if v:
                model = self._get_model(k)
                qs = model.objects.year(year_from)
                if not qs.exists():
                    self._append_error_message(msg, errors, k)

        # copy to table must be empty
        msg = _('%(year)s year already has plans.') % ({'year': year_to})

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


        # labels
        self.fields['year_from'].label = _('Copy from')
        self.fields['year_to'].label = _('Copy to')
        self.fields['income'].label = _('Incomes plans')
        self.fields['expense'].label = _('Expenses plans')
        self.fields['saving'].label = _('Savings plans')
        self.fields['day'].label = _('Day plans')
        self.fields['necessary'].label = _('Plans for additional necessary expenses')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
