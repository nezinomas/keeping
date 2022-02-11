from datetime import datetime

from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.helpers.helper_forms import ChainedDropDown, set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from ..core.mixins.forms import YearBetweenMixin
from .models import SavingChange, SavingClose, SavingType, Transaction


class TransactionForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'from_account', 'to_account', 'price']

    field_order = ['date', 'from_account', 'to_account', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        # initial values
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['price'].label = _('Amount')
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['from_account'].queryset = Account.objects.items()
        self.fields['to_account'].queryset = Account.objects.items()

        # field labels
        self.fields['date'].label = _('Date')
        self.fields['from_account'].label = _('From account')
        self.fields['to_account'].label = _('To account')

        # chained dropdown
        _id = ChainedDropDown(self, 'from_account').parent_field_id
        if _id:
            self.fields['to_account'].queryset = (
                Account.objects.items().exclude(pk=_id)
            )

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class SavingCloseForm(YearBetweenMixin, forms.ModelForm):
    close = forms.BooleanField(required=False)

    class Meta:
        model = SavingClose
        fields = ['date', 'from_account', 'to_account', 'price', 'fee', 'close']

    field_order = ['date', 'from_account', 'to_account', 'price', 'fee', 'close']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        # form input settings
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['fee'].widget.attrs = {'step': '0.01'}

        # form initial values
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['from_account'].queryset = SavingType.objects.items()
        self.fields['to_account'].queryset = Account.objects.items()

        # form fields labels
        self.fields['price'].label = _('Amount')
        # 'Suma kuri lieka atskaičius mokesčius'
        self.fields['price'].help_text = _('Amount left after fee')
        self.fields['fee'].label = _('Fees')
        self.fields['date'].label = _('Date')
        self.fields['from_account'].label = _('From account')
        self.fields['to_account'].label = _('To account')
        self.fields['close'].label = mark_safe(f"{_('Close')} <b>{_('From account')}</b>")

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['close'].widget.attrs['class'] = " form-check-input"

    def save(self):
        close = self.cleaned_data.get('close')

        if close:
            obj = SavingType.objects.get(pk=self.instance.from_account.pk)
            obj.closed = datetime.now().year
            obj.save()

        return super().save()


class SavingChangeForm(YearBetweenMixin, forms.ModelForm):
    close = forms.BooleanField(required=False)

    class Meta:
        model = SavingChange
        fields = ['date', 'from_account', 'to_account', 'price', 'fee', 'close']

    field_order = ['date', 'from_account', 'to_account', 'price', 'fee', 'close']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        # form input settings
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['fee'].widget.attrs = {'step': '0.01'}

        # initial values
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['from_account'].queryset = SavingType.objects.items()
        self.fields['to_account'].queryset = SavingType.objects.items()

        # fields labels
        self.fields['price'].label = _('Amount')
        self.fields['price'].help_text = _('Amount left after fee')
        self.fields['fee'].label = _('Fees')
        self.fields['date'].label = _('Date')
        self.fields['from_account'].label = _('From account')
        self.fields['to_account'].label = _('To account')
        self.fields['close'].label = mark_safe(f"{_('Close')} <b>{_('From account')}</b>")

        # chained dropdown
        _id = ChainedDropDown(self, 'from_account').parent_field_id
        if _id:
            self.fields['to_account'].queryset = (
                SavingType
                .objects
                .related()
                .exclude(pk=_id)
            )

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['close'].widget.attrs['class'] = " form-check-input"

    def save(self):
        close = self.cleaned_data.get('close')

        if close:
            obj = SavingType.objects.get(pk=self.instance.from_account.pk)
            obj.closed = datetime.now().year
            obj.save()

        return super().save()
