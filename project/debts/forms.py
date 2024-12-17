from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.lib import utils
from ..core.lib.convert_price import ConvertToPrice
from ..core.lib.date import set_year_for_form
from ..core.mixins.forms import YearBetweenMixin
from . import models


class DebtForm(ConvertToPrice, YearBetweenMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0.01)

    class Meta:
        model = models.Debt
        fields = ["journal", "date", "name", "price", "closed", "account", "remark"]

    field_order = ["date", "account", "name", "price", "remark", "closed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerInput(
            options={
                "locale": utils.get_user().journal.lang,
            }
        )

        # form inputs settings
        self.fields["remark"].widget.attrs["rows"] = 3

        # journal input
        self.fields["journal"].initial = utils.get_user().journal
        self.fields["journal"].disabled = True
        self.fields["journal"].widget = forms.HiddenInput()

        # inital values
        self.fields["account"].initial = Account.objects.items().first()
        self.fields["date"].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields["account"].queryset = Account.objects.items()

        # fields labels
        debt_type = utils.get_request_kwargs("debt_type")
        _name = _("Debtor")

        if debt_type == "lend":
            _name = _("Borrower")

        if debt_type == "borrow":
            _name = _("Lender")

        self.fields["date"].label = _("Date")
        self.fields["name"].label = _name
        self.fields["account"].label = _("Account")
        self.fields["price"].label = _("Sum")
        self.fields["remark"].label = _("Remark")
        self.fields["closed"].label = _("Returned")

        self.helper = FormHelper()

    def save(self, *args, **kwargs):
        # set debt_type
        if not self.instance.pk:
            self.instance.debt_type = utils.get_request_kwargs("debt_type") or "lend"
        return super().save(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        closed = cleaned_data.get("closed")
        price = cleaned_data.get("price")

        # can't update name
        if not closed and name != self.instance.name:
            qs = models.Debt.objects.items().filter(name=name)
            if qs.exists():
                self.add_error("name", _("The name of the lender must be unique."))

        # can't close not returned debt
        _msg_cant_close = _("You can't close a debt that hasn't been returned.")
        if not self.instance.pk and closed:
            self.add_error("closed", _msg_cant_close)

        if self.instance.pk and closed and self.instance.returned / 100 != price:
            self.add_error("closed", _msg_cant_close)

        # can't update to smaller price
        if self.instance.pk and price < self.instance.returned / 100:
            self.add_error(
                "price",
                _("The amount due exceeds the debt."),
            )

        return cleaned_data


class DebtReturnForm(ConvertToPrice, YearBetweenMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0.01)

    class Meta:
        model = models.DebtReturn
        fields = ["date", "price", "remark", "account", "debt"]

    field_order = ["date", "account", "debt", "price", "remark"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerInput(
            options={
                "locale": utils.get_user().journal.lang,
            }
        )

        # form inputs settings
        self.fields["remark"].widget.attrs["rows"] = 3

        # inital values
        self.fields["date"].initial = set_year_for_form()
        self.fields["account"].initial = Account.objects.items().first()

        # overwrite ForeignKey expense_type queryset
        self.fields["account"].queryset = Account.objects.items()
        self.fields["debt"].queryset = models.Debt.objects.items().filter(closed=False)

        # fields labels
        debt_type = utils.get_request_kwargs("debt_type")
        _name = _("Debtor")

        if debt_type == "lend":
            _name = _("Borrower")

        if debt_type == "borrow":
            _name = _("Lender")

        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("Account")
        self.fields["debt"].label = _name
        self.fields["price"].label = _("Sum")
        self.fields["remark"].label = _("Remark")

        self.helper = FormHelper()

    def clean_price(self):
        price = self.cleaned_data["price"]
        debt = self.cleaned_data.get("debt")

        if not debt:
            return price

        qs = (
            models.DebtReturn.objects.related()
            .filter(debt=debt)
            .exclude(pk=self.instance.pk)
            .aggregate(Sum("price"))
        )

        price_sum = qs.get("price__sum") or 0

        if price > (debt.price / 100 - price_sum / 100):
            msg = _("The amount due exceeds the debt.")
            raise ValidationError(msg)

        return price

    def clean(self):
        cleaned_data = super().clean()

        date = cleaned_data.get("date")
        debt = cleaned_data.get("debt")
        if debt and date < debt.date:
            self.add_error("date", _("The date preceding the debt's date."))

        return cleaned_data
