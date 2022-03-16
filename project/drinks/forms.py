from datetime import datetime

from bootstrap_datepicker_plus.widgets import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _
from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from ..core.mixins.forms import YearBetweenMixin
from .apps import App_name
from .models import MAX_BOTTLES, Drink, DrinkTarget, DrinkType


class DrinkForm(YearBetweenMixin, forms.ModelForm):
    option = forms.ChoiceField(
        choices=DrinkType.choices,
        initial=DrinkType.BEER,
        widget=forms.Select(),
        required=True
    )

    class Meta:
        model = Drink
        fields = ['user', 'date', 'quantity', 'option']

    field_order = ['date', 'option', 'quantity']

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

        self.fields['date'].label = _('Date')
        self.fields['option'].label = _('Drink type')
        self.fields['quantity'].label = _('Quantity')

        _h1 = _('1 Beer = 0.5L')
        _h2 = _('1 Wine = 0.75L')
        _h3 = _('1 Vodka = 1L')
        _h4 = _('If more than %(cnt)s is entered, it will be assumed to be mL') % {'cnt': MAX_BOTTLES}
        _help_text = f'{_h1}</br>{_h2}</br>{_h3}</br></br>{_h4}'
        self.fields['quantity'].help_text = _help_text

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        instance.counter_type = App_name
        instance.save()

        return instance


class DrinkTargetForm(forms.ModelForm):
    class Meta:
        model = DrinkTarget
        fields = ['user', 'year', 'drink_type', 'quantity']

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'drink_type', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # user input
        self.fields['user'].initial = utils.get_user()
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

        # inital values
        self.fields['year'].initial = set_year_for_form()

        self.fields['year'].label = _('Year')
        self.fields['quantity'].label = _('Quantity') + ', ml'
        self.fields['drink_type'].label = _('Drink type')

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
            msg = _('already has a goal.')
            raise forms.ValidationError(f'{year} {msg}')

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
            raise forms.ValidationError(_('Must be 4 digits.'))
