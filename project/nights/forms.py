from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib.date import set_year_for_form
from ..core.mixins.form_mixin import FormForUserMixin
from .apps import App_name
from .models import Night


class NightForm(FormForUserMixin, forms.ModelForm):
    class Meta:
        model = Night
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
        self.fields['quantity'].label = 'Kiek'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        instance.counter_type = App_name
        instance.save()

        return instance
