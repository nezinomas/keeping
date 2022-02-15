from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from ..core.mixins.forms import YearBetweenMixin
from . import models


class DebtForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = models.Debt
        fields = ['journal', 'date', 'name', 'price', 'closed', 'account', 'remark']

    field_order = ['date', 'name', 'price', 'account', 'remark', 'closed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        # form inputs settings
        self.fields['remark'].widget.attrs['rows'] = 3

        # journal input
        self.fields['journal'].initial = utils.get_user().journal
        self.fields['journal'].disabled = True
        self.fields['journal'].widget = forms.HiddenInput()

        # inital values
        self.fields['account'].initial = Account.objects.items().first()
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['account'].queryset = Account.objects.items()

        # fields labels
        _type = utils.get_request_kwargs("type")
        _name = _('Debtor')

        if _type == 'lend':
            _name = _('Borrower')

        if _type == 'borrow':
            _name = _('Lender')

        self.fields['date'].label = _('Date')
        self.fields['name'].label = _name
        self.fields['account'].label = _('Account')
        self.fields['price'].label = _('Sum')
        self.fields['remark'].label = _('Remark')
        self.fields['closed'].label = _('Returned')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['closed'].widget.attrs['class'] = " form-check-input"

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)

        type = utils.get_request_kwargs("type")
        type = type if type else 'lend'
        instance.type = type

        instance.save()

        return instance

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get('name')
        closed = cleaned_data.get('closed')
        price = cleaned_data.get('price')

        # can't update name
        if not closed:
            if name != self.instance.name:
                qs = models.Debt.objects.items().filter(name=name)
                if qs.exists():
                    self.add_error('name', _('The name of the lender must be unique.'))

        # can't close not returned debt
        _msg_cant_close = _("You can't close a debt that hasn't been returned.")
        if not self.instance.pk and closed:
            self.add_error('closed', _msg_cant_close)

        if self.instance.pk and closed:
            if self.instance.returned != price:
                self.add_error('closed', _msg_cant_close)

        # can't update to smaller price
        if self.instance.pk:
            if price < self.instance.returned:
                self.add_error('price', _("You cannot update to an amount lower than the amount already returned."))

        return


class DebtReturnForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = models.DebtReturn
        fields = ['date', 'price', 'remark', 'account', 'debt']

    field_order = ['date', 'debt', 'account', 'price', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        # form inputs settings
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['date'].initial = set_year_for_form()
        self.fields['account'].initial = Account.objects.items().first()

        # overwrite ForeignKey expense_type queryset
        self.fields['account'].queryset = Account.objects.items()
        self.fields['debt'].queryset = models.Debt.objects.items().filter(closed=False)

        # fields labels
        self.fields['date'].label = _('Date')
        self.fields['account'].label = _('Account')
        self.fields['debt'].label = _('Lender')
        self.fields['price'].label = _('Sum')
        self.fields['remark'].label = _('Remark')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean_price(self):
        price = self.cleaned_data['price']
        debt = self.cleaned_data.get('debt')

        if debt:
            obj = models.Debt.objects.related().get(pk=debt.pk)

            if price > (obj.price - obj.returned):
                raise ValidationError(_('The amount to be paid is more than the debt!'))

        return price

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        debt = cleaned_data.get('debt')

        if debt:
            if date < debt.date:
                self.add_error('date', _('The date is earlier than the date of the debt.'))
