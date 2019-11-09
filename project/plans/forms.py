import calendar
from datetime import datetime

from bootstrap_datepicker_plus import YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.apps import apps
from django.core.validators import MaxValueValidator, MinValueValidator

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib.date import monthnames
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

        self.fields['saving_type'].queryset = SavingType.objects.items(year)

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
        for k, v in dict_.items():
            if v:
                model = self._get_model(k)
                qs = model.objects.year(year_from)
                if not qs.exists():
                    msg = ['Nėra ką kopijuoti.']
                    raise forms.ValidationError({k: msg})

        # copy to table must be empty
        for k, v in dict_.items():
            if v:
                model = self._get_model(k)
                qs = model.objects.year(year_to)
                if qs.exists():
                    msg = [f'{year_to} metai jau turi planus.']
                    raise forms.ValidationError({k: msg})

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

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # initail values
        self.fields['income'].initial = True
        self.fields['expense'].initial = True
        self.fields['saving'].initial = True
        self.fields['day'].initial = True
        self.fields['necessary'].initial = True

        # fields labels
        self.fields['year_from'].label = 'Kopijuoti iš'
        self.fields['year_to'].label = 'Kopijuoti į'
        self.fields['income'].label = 'Pajamų planus'
        self.fields['expense'].label = 'Išlaidų planus'
        self.fields['saving'].label = 'Taupymo planus'
        self.fields['day'].label = 'Dienos planus'
        self.fields['necessary'].label = 'Papildomų būtinų išlaidų planus'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
