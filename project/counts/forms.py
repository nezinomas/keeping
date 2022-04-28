from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from ..core.mixins.forms import YearBetweenMixin
from .models import Count, CountType


class CountForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = Count
        fields = ['user', 'date', 'quantity', 'count_type']

    field_order = ['date', 'count_type', 'quantity']

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

    def clean_title(self):
        reserved_titles = ['none', 'type', 'delete', 'update']
        title = self.cleaned_data['title']

        if title and title.lower() in reserved_titles:
            self.add_error(
                'title',
                _('This title is reserved for the system.')
            )

        return title
