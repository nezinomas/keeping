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


class BorrowForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = models.Borrow
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
        self.fields['date'].label = _('Date')
        self.fields['name'].label = _('Borrower')
        self.fields['account'].label = _('Account')
        self.fields['price'].label = _('Sum')
        self.fields['remark'].label = _('Remark')
        self.fields['closed'].label = _('Returned')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['closed'].widget.attrs['class'] = " form-check-input"

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get('name')
        closed = cleaned_data.get('closed')
        price = cleaned_data.get('price')

        # can't update name
        if not closed:
            if name != self.instance.name:
                qs = models.Borrow.objects.items().filter(name=name)
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


class BorrowReturnForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = models.BorrowReturn
        fields = ['date', 'price', 'remark', 'account', 'borrow']

    field_order = ['date', 'borrow', 'account', 'price', 'remark']

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
        self.fields['borrow'].queryset = models.Borrow.objects.items().filter(closed=False)
        self.fields['account'].queryset = Account.objects.items()

        # fields labels
        self.fields['date'].label = _('Date')
        self.fields['account'].label = _('Account')
        self.fields['borrow'].label = _('Borrower')
        self.fields['price'].label = _('Sum')
        self.fields['remark'].label = _('Remark')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean_price(self):
        price = self.cleaned_data['price']
        borrow = self.cleaned_data.get('borrow')

        if borrow:
            obj = models.Borrow.objects.related().get(pk=borrow.pk)

            if price > (obj.price - obj.returned):
                raise ValidationError(_('The amount to be paid is more than the debt!'))

        return price

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        borrow = cleaned_data.get('borrow')

        if borrow:
            if date < borrow.date:
                self.add_error('date', _('The date is earlier than the date of the debt.'))


class LentForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = models.Lent
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
        self.fields['date'].label = _('Date')
        self.fields['name'].label = _('Lender')
        self.fields['account'].label = _('Account')
        self.fields['price'].label = _('Sum')
        self.fields['remark'].label = _('Remark')
        self.fields['closed'].label = _('Returned')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['closed'].widget.attrs['class'] = " form-check-input"

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get('name')
        closed = cleaned_data.get('closed')
        price = cleaned_data.get('price')

        # can't update name
        if not closed:
            if name != self.instance.name:
                qs = models.Lent.objects.items().filter(name=name)
                if qs.exists():
                    self.add_error('name', _('The name of the lender must be unique.'))

        # can't close not returned debt
        _msg_cant_close = _(
            "You can't close a debt that hasn't been returned.")
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


class LentReturnForm(YearBetweenMixin, forms.ModelForm):
    class Meta:
        model = models.LentReturn
        fields = ['date', 'price', 'remark', 'account', 'lent']

    field_order = ['date', 'lent', 'account', 'price', 'remark']

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
        self.fields['lent'].queryset = models.Lent.objects.items().filter(closed=False)

        # fields labels
        self.fields['date'].label = _('Date')
        self.fields['account'].label = _('Account')
        self.fields['lent'].label = _('Lender')
        self.fields['price'].label = _('Sum')
        self.fields['remark'].label = _('Remark')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean_price(self):
        price = self.cleaned_data['price']
        lent = self.cleaned_data.get('lent')

        if lent:
            obj = models.Lent.objects.related().get(pk=lent.pk)

            if price > (obj.price - obj.returned):
                raise ValidationError(_('The amount to be paid is more than the debt!'))

        return price

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        lent = cleaned_data.get('lent')

        if lent:
            if date < lent.date:
                self.add_error('date', _('The date is earlier than the date of the debt.'))