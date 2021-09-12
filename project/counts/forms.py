from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from .apps import App_name
from .models import Count, CountType


class CountForm(forms.ModelForm):
    class Meta:
        model = Count
        fields = ['user', 'date', 'quantity']

    field_order = ['date', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        # user input
        self.fields['user'].initial = utils.get_user()
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

        # inital values
        self.fields['date'].initial = set_year_for_form()
        self.fields['quantity'].initial = 1

        self.fields['date'].label = _('Date')
        self.fields['quantity'].label = _('Quantity')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        instance.counter_type = utils.get_request_kwargs("count_type")
        instance.save()

        return instance


class CountTypeForm(forms.ModelForm):
    class Meta:
        model = CountType
        fields = ['user', 'title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # user input
        self.fields['user'].initial = utils.get_user()
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

        self.fields['title'].label = _('Title')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
