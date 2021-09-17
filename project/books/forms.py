from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form, years
from .models import Book, BookTarget


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['user', 'started', 'ended', 'author', 'title', 'remark']

    field_order = ['started', 'ended', 'author', 'title', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = utils.get_user()
        lang = user.journal.lang

        self.fields['started'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": lang,
            }).start_of('event days')

        self.fields['ended'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": lang,
            }).end_of('event days')

        # user input
        self.fields['user'].initial = user
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

        # inital values
        self.fields['started'].initial = set_year_for_form()

        self.fields['started'].label = _('Started reading')
        self.fields['ended'].label = _('Ended reading')
        self.fields['title'].label = _('Title')
        self.fields['author'].label = _('Author')
        self.fields['remark'].label = _('Remark')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean_started(self):
        dt = self.cleaned_data['started']

        if dt:
            year_instance = dt.year
            years_ = years()[:-1]
            if year_instance not in years_:
                self.add_error(
                    'started',
                    _('Year must be between %(year1)s and %(year2)s')
                    % ({'year1':  years_[0], 'year2': years_[-1]})
                )

            if dt > datetime.now().date():
                self.add_error(
                    'started',
                    _('Date cannot be in the future')
                )

        return dt

    def clean_ended(self):
        dt = self.cleaned_data['ended']

        if dt:
            if dt > datetime.now().date():
                self.add_error(
                    'ended',
                    _('Date cannot be in the future')
                )

        return dt

    def clean(self):
        cleaned = super().clean()

        started = cleaned.get('started')
        ended = cleaned.get('ended')

        if ended:
            if ended < started:
                self.add_error(
                    'ended',
                    _('Ended reading cannot precede started reading')
                )


class BookTargetForm(forms.ModelForm):
    class Meta:
        model = BookTarget
        fields = ['user', 'year', 'quantity']

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # user input
        self.fields['user'].initial = utils.get_user()
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

        # inital values
        self.fields['year'].initial = set_year_for_form()

        self.fields['year'].label = _('Year')
        self.fields['quantity'].label = _('How many')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean_year(self):
        year = self.cleaned_data['year']

        # if update
        if self.instance.pk:
            return year

        # if new record
        qs = BookTarget.objects.year(year)
        if qs.exists():
            msg = _("already has a goal.")
            raise forms.ValidationError(f'{year} {msg}')

        return year
