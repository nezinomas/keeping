from datetime import datetime

from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
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

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def _initial_fields_values(self):
        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        # initial values
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['price'].label = _('Amount')
        self.fields['date'].initial = set_year_for_form()

    def _overwrite_default_queries(self):
        from_account = self.fields['from_account']
        to_account = self.fields['to_account']

        from_account.queryset = Account.objects.items()
        to_account.queryset = Account.objects.items()

        if not self.instance.pk:
            from_account_pk = self.data.get('from_account')
        else:
            from_account_pk = self.instance.from_account.pk

        try:
            from_account_pk = int(from_account_pk)
        except (ValueError, TypeError):
            from_account_pk = None

        if from_account_pk:
            to_account.queryset = \
                Account.objects \
                .items() \
                .exclude(pk=from_account_pk)

    def _set_htmx_attributes(self):
        url = reverse('accounts:load')

        field = self.fields['from_account']
        field.widget.attrs['hx-get'] = url
        field.widget.attrs['hx-target'] = '#id_to_account'
        field.widget.attrs['hx-trigger'] = 'change'

    def _translate_fields(self):
        self.fields['date'].label = _('Date')
        self.fields['from_account'].label = _('From account')
        self.fields['to_account'].label = _('To account')


class SavingCloseForm(YearBetweenMixin, forms.ModelForm):
    close = forms.BooleanField(required=False)

    class Meta:
        model = SavingClose
        fields = ['date', 'from_account', 'to_account', 'price', 'fee', 'close']

    field_order = ['date', 'from_account', 'to_account', 'price', 'fee', 'close']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._translate_fields()
        self._set_css_classes()

    def _initial_fields_values(self):
        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['fee'].widget.attrs = {'step': '0.01'}

        self.fields['date'].initial = set_year_for_form()

    def _overwrite_default_queries(self):
        self.fields['from_account'].queryset = SavingType.objects.items()
        self.fields['to_account'].queryset = Account.objects.items()

    def _translate_fields(self):
        self.fields['price'].label = _('Amount')
        self.fields['price'].help_text = _('Amount left after fee')
        self.fields['fee'].label = _('Fees')
        self.fields['date'].label = _('Date')
        self.fields['from_account'].label = _('From account')
        self.fields['to_account'].label = _('To account')
        self.fields['close'].label = mark_safe(f"{_('Close')} <b>{_('From account')}</b>")

    def _set_css_classes(self):
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

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()
        self._set_css_classes()

    def _initial_fields_values(self):
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

    def _overwrite_default_queries(self):
        from_account = self.fields['from_account']
        to_account = self.fields['to_account']

        from_account.queryset = SavingType.objects.items()
        to_account.queryset = SavingType.objects.items()

        if not self.instance.pk:
            from_account_pk = self.data.get('from_account')
        else:
            from_account_pk = self.instance.from_account.pk

        try:
            from_account_pk = int(from_account_pk)
        except (ValueError, TypeError):
            from_account_pk = None

        if from_account_pk:
            to_account.queryset = \
                SavingType.objects \
                .items() \
                .exclude(pk=from_account_pk)

    def _set_htmx_attributes(self):
        url = reverse('transactions:load_saving_type')

        field = self.fields['from_account']
        field.widget.attrs['hx-get'] = url
        field.widget.attrs['hx-target'] = '#id_to_account'
        field.widget.attrs['hx-trigger'] = 'change'

    def _translate_fields(self):
        self.fields['price'].label = _('Amount')
        self.fields['price'].help_text = _('Amount left after fee')
        self.fields['fee'].label = _('Fees')
        self.fields['date'].label = _('Date')
        self.fields['from_account'].label = _('From account')
        self.fields['to_account'].label = _('To account')
        self.fields['close'].label = mark_safe(f"{_('Close')} <b>{_('From account')}</b>")

    def _set_css_classes(self):
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
