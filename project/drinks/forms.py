from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from .models import Drink


class DrinkForm(forms.ModelForm):
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

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['date'].initial = datetime.now()

        self.fields['date'].label = 'Data'
        self.fields['quantity'].label = 'Kiekis (0,5L alaus)'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
