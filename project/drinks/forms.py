from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib.date import set_year_for_form
from ..core.mixins.form_mixin import FormForUserMixin
from .apps import App_name
from .models import Drink, DrinkTarget


class DrinkForm(FormForUserMixin, forms.ModelForm):
    class Meta:
        model = Drink
        fields = ['date', 'quantity']

        widgets = {
            'date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['date', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['date'].initial = set_year_for_form()

        self.fields['date'].label = 'Data'
        self.fields['quantity'].label = 'Kiekis (0,5L alaus)'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        instance.counter_type = App_name
        instance.save()

        return instance



class DrinkTargetForm(FormForUserMixin, forms.ModelForm):
    class Meta:
        model = DrinkTarget
        fields = ['year', 'quantity']

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['year'].initial = set_year_for_form()

        self.fields['year'].label = 'Metai'
        self.fields['quantity'].label = 'Kiekis ml'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean_year(self):
        year = self.cleaned_data['year']

        # if update
        if self.instance.pk:
            return year

        # if new record
        qs = DrinkTarget.objects.year(year)
        if qs.exists():
            raise forms.ValidationError(f'{year} metai jau turi tikslą.')

        return year


class DrinkCompareForm(forms.Form):
    year1 = forms.IntegerField()
    year2 = forms.IntegerField()

    field_order = ['year1', 'year2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['year1'].label = None
        self.fields['year2'].label = None

        # inital values
        self.fields['year2'].initial = datetime.now().year

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean_year1(self):
        year = self.cleaned_data['year1']

        self._validation_error(year)

        return year

    def clean_year2(self):
        year = self.cleaned_data['year2']

        self._validation_error(year)

        return year

    def _validation_error(self, field):
        if len(str(abs(field))) != 4:
            raise forms.ValidationError('Turi būti 4 skaitmenys.')
