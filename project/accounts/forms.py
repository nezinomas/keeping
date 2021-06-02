from bootstrap_datepicker_plus import YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['user', 'title', 'closed', 'order']
        widgets = {
            'closed': YearPickerInput(
                options={
                    "format": "YYYY",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['title', 'order', 'closed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # user input
        self.fields['user'].initial = utils.get_user()
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['title'].label = 'Sąskaitos pavadinimas'
        self.fields['closed'].label = 'Uždaryta'
        self.fields['order'].label = 'Rūšiavimas'
