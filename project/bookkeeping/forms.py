from datetime import datetime
from zoneinfo import ZoneInfo

from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..expenses.models import ExpenseType
from ..pensions.models import PensionType
from ..savings.models import SavingType
from .models import AccountWorth, PensionWorth, SavingWorth


class DateForm(forms.Form):
    date = forms.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = utils.get_user()
        lang = user.journal.lang

        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": lang,
            })

        # inital values
        self.fields['date'].initial = datetime.now()

        # label
        self.fields['date'].label = _('Date')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get('date')

        if not date:
            date = datetime.now()

        cleaned['date'] = datetime.combine(date, datetime.now().time(), tzinfo=ZoneInfo(key='UTC'))

        return cleaned


class SavingWorthForm(forms.ModelForm):
    class Meta:
        model = SavingWorth
        fields = ['date', 'saving_type', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form initial values
        self.fields['price'].initial = '0'
        self.fields['date'].initial = datetime.now()

        # overwrite FK
        self.fields['saving_type'].queryset = SavingType.objects.items()

        self.fields['date'].disabled = True
        self.fields['date'].widget = forms.HiddenInput()

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class AccountWorthForm(forms.ModelForm):
    class Meta:
        model = AccountWorth
        fields = ['date', 'account', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form initial values
        self.fields['price'].initial = '0'
        self.fields['date'].initial = datetime.now()

        # overwrite FK
        self.fields['account'].queryset = Account.objects.items()

        self.fields['date'].disabled = True
        self.fields['date'].widget = forms.HiddenInput()

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class PensionWorthForm(forms.ModelForm):
    class Meta:
        model = PensionWorth
        fields = ['date', 'pension_type', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['price'].initial = '0'
        self.fields['date'].initial = datetime.now()

        # overwrite FK
        self.fields['pension_type'].queryset = PensionType.objects.items()

        self.fields['date'].disabled = True
        self.fields['date'].widget = forms.HiddenInput()

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class SummaryExpensesForm(forms.Form):
    types = forms.MultipleChoiceField(
        required=False
    )
    names = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []
        for _type in ExpenseType.objects.items():
            choices.append((_type.id, _type.title))

            for _name in _type.expensename_set.all():
                choices.append((f'{_type.id}:{_name.id}', _name.title))

        self.fields['types'].choices = choices
        self.fields['types'].label = None

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean(self):
        cleaned_data = super().clean()
        _types = cleaned_data.get('types')
        _names = cleaned_data.get('names')

        if not _types and not _names:
            raise forms.ValidationError(
                _('At least one category needs to be selected.')
            )
        return cleaned_data
