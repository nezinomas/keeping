from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils.translation import gettext as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import ConvertToPrice
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_widgets import DatePickerWidget
from ..core.mixins.forms import YearBetweenMixin
from . import models
from .services.model_services import DebtModelService, DebtReturnModelService


class DebtForm(ConvertToPrice, YearBetweenMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0.01)

    class Meta:
        model = models.Debt
        fields = ["journal", "date", "name", "price", "closed", "account", "remark"]

    field_order = ["date", "account", "name", "price", "remark", "closed"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.debt_type = kwargs.pop("debt_type")

        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerWidget()

        # form inputs settings
        self.fields["remark"].widget.attrs["rows"] = 3

        # journal input
        self.fields["journal"].initial = self.user.journal
        self.fields["journal"].disabled = True
        self.fields["journal"].widget = forms.HiddenInput()

        accounts = AccountModelService(self.user).items()
        # inital values
        self.fields["account"].initial = accounts.first()
        self.fields["date"].initial = set_date_with_user_year(self.user)

        # overwrite ForeignKey expense_type queryset
        self.fields["account"].queryset = accounts

        # fields labels
        _name = _("Debtor")

        if self.debt_type == "lend":
            _name = _("Borrower")

        if self.debt_type == "borrow":
            _name = _("Lender")

        self.fields["date"].label = _("Date")
        self.fields["name"].label = _name
        self.fields["account"].label = _("Account")
        self.fields["price"].label = _("Sum")
        self.fields["remark"].label = _("Remark")
        self.fields["closed"].label = _("Returned")

    def save(self, *args, **kwargs):
        # set debt_type
        if not self.instance.pk:
            self.instance.debt_type = self.debt_type

        return super().save(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        closed = cleaned_data.get("closed")
        price = cleaned_data.get("price")

        # can't update name
        if not closed and name != self.instance.name:
            qs = DebtModelService(self.user, self.debt_type).items().filter(name=name)
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
        self.user = kwargs.pop("user", None)
        self.debt_type = kwargs.pop("debt_type", None)
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerWidget()

        # form inputs settings
        self.fields["remark"].widget.attrs["rows"] = 3

        accounts = AccountModelService(self.user).items()
        # inital values
        self.fields["date"].initial = set_date_with_user_year(self.user)
        self.fields["account"].initial = accounts.first()

        # overwrite ForeignKey expense_type queryset
        self.fields["account"].queryset = accounts
        self.fields["debt"].queryset = (
            DebtModelService(self.user, self.debt_type).items().filter(closed=False)
        )

        # fields labels
        _name = _("Debtor")

        if self.debt_type == "lend":
            _name = _("Borrower")

        if self.debt_type == "borrow":
            _name = _("Lender")

        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("Account")
        self.fields["debt"].label = _name
        self.fields["price"].label = _("Sum")
        self.fields["remark"].label = _("Remark")

    def clean_price(self):
        price = self.cleaned_data["price"]
        debt = self.cleaned_data.get("debt")

        if not debt:
            return price

        qs = (
            DebtReturnModelService(self.user, self.debt_type)
            .objects.filter(debt=debt)
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
