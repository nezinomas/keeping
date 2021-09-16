from bootstrap_datepicker_plus import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form, years
from .models import Saving, SavingType


class SavingTypeForm(forms.ModelForm):
    class Meta:
        model = SavingType
        fields = ['journal', 'title', 'type', 'closed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['closed'].widget = YearPickerInput(
            options={
                "format": "YYYY",
                "locale": utils.get_user().journal.lang,
            })

        # journal input
        self.fields['journal'].initial = utils.get_user().journal
        self.fields['journal'].disabled = True
        self.fields['journal'].widget = forms.HiddenInput()

        self.fields['title'].label = _('Fund')
        self.fields['closed'].label = _('Closed')
        self.fields['type'].label = _('Type')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class SavingForm(forms.ModelForm):
    class Meta:
        model = Saving
        fields = ['date', 'price', 'fee', 'remark', 'saving_type', 'account']

    field_order = ['date', 'saving_type', 'account', 'price', 'fee', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        # form inputs settings
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['fee'].widget.attrs = {'step': '0.01'}
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['account'].initial = Account.objects.items().first()
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey saving_type and account queryset
        self.fields['saving_type'].queryset = SavingType.objects.items()
        self.fields['account'].queryset = Account.objects.items()

        self.fields['date'].label = _('Date')
        self.fields['account'].label = _('From account')
        self.fields['price'].label = _('Sum')
        self.fields['fee'].label = _('Fees')
        self.fields['remark'].label = _('Remark')
        self.fields['saving_type'].label = _('Fund')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean_date(self):
        dt = self.cleaned_data['date']

        if dt:
            year_instance = dt.year
            years_ = years()

            if year_instance not in years_:
                self.add_error(
                    'date',
                    _('Year must be between %(year1)s and %(year2)s')
                    % ({'year1':  years_[0], 'year2': years_[-1]})
                )

        return dt
