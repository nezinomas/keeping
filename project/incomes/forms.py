from datetime import datetime

from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.core.validators import MinValueValidator
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.helpers.helper_forms import add_css_class
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from .models import Income, IncomeType


class IncomeForm(forms.ModelForm):
    price = forms.FloatField(validators=[MinValueValidator(0.01)])

    class Meta:
        model = Income
        fields = ('date', 'price', 'remark', 'account', 'income_type')

    field_order = ['date', 'income_type', 'account', 'price', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget = DatePickerInput(
            options={"locale": utils.get_user().journal.lang,}
        )

        # form inputs settings
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['account'].initial = Account.objects.items().first()
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['income_type'].queryset = IncomeType.objects.items()
        self.fields['account'].queryset = Account.objects.items()

        self.fields['date'].label = _('Date')
        self.fields['account'].label = _('Account')
        self.fields['price'].label = _('Amount')
        self.fields['remark'].label = _('Remark')
        self.fields['income_type'].label = _('Incomes type')

        self.helper = FormHelper()
        add_css_class(self, self.helper)

    def clean_date(self):
        dt = self.cleaned_data['date']

        if dt:
            year_user = utils.get_user().year
            year_instance = dt.year
            year_now = datetime.now().year

            diff = 3
            if (year_user - year_instance) > diff:
                year_msg = year_user - diff
                self.add_error(
                    'date',
                    _('Year cannot be less than %(year)s') % ({'year': year_msg })
                )

            diff = 1
            if (year_instance - year_now) > diff:
                year_msg = year_user + diff
                self.add_error(
                    'date',
                    _('Year cannot be greater than %(year)s') % ({'year': year_msg })
                )

        return dt

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        instance.price = int(self.cleaned_data.get('price') * 100)
        instance.save()
        return instance


class IncomeTypeForm(forms.ModelForm):
    class Meta:
        model = IncomeType
        fields = ['journal', 'title', 'type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # user input
        self.fields['journal'].initial = utils.get_user().journal
        self.fields['journal'].disabled = True
        self.fields['journal'].widget = forms.HiddenInput()

        self.fields['title'].label = _('Incomes type')
        self.fields['type'].label = _('Type')

        self.helper = FormHelper()
        add_css_class(self, self.helper)
