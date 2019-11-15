from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.mixins.form_mixin import FormMixin
from .models import Drink, DrinkTarget


class DrinkForm(FormMixin, forms.ModelForm):
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
        self.fields['date'].initial = datetime.now()

        self.fields['date'].label = 'Data'
        self.fields['quantity'].label = 'Kiekis (0,5L alaus)'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class DrinkTargetForm(FormMixin, forms.ModelForm):
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
        self.fields['year'].initial = datetime.now()

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
