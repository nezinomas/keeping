from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from ..accounts.forms import ACCOUNT_CLOSED
from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import PriceToCentsFormMixin, float_to_int_cents
from ..core.lib.form_fields import CommaFloatField, date_field, pin
from ..core.mixins.forms import ClosedYearMixin, UserTodayMixin, YearBetweenMixin
from . import models
from .services.model_services import DebtModelService, DebtReturnModelService

CANT_CLOSE = gettext_lazy("You can't close a debt that hasn't been returned.")


def _other_party_label(debt_type):
    return {
        models.Debt.DebtType.LEND: _("Borrower"),
        models.Debt.DebtType.BORROW: _("Lender"),
    }[debt_type]


class DebtFormMixin(
    UserTodayMixin, ClosedYearMixin, PriceToCentsFormMixin, YearBetweenMixin
):
    """The date, account and remark every debt form sets up and checks the same way."""

    closed_fields = {"account": (ACCOUNT_CLOSED, "date")}

    def __init__(self, *args, **kwargs):
        self.debt_type = kwargs.pop("debt_type")

        super().__init__(*args, **kwargs)

        self.remark_field_settings()
        self.date_field_settings()
        self.account_field_settings()

    def remark_field_settings(self):
        self.fields["remark"].widget.attrs["rows"] = 3

    def date_field_settings(self):
        date_field(self.fields["date"], self.user, self.today)

    def account_field_settings(self):
        accounts = AccountModelService(self.user).items()

        if account := accounts.first():
            self.fields["account"].initial = account
        self.fields["account"].queryset = accounts


class DebtForm(DebtFormMixin, forms.ModelForm):
    price_fields = ("price",)
    price = CommaFloatField(min_value=0.01)

    class Meta:
        model = models.Debt
        fields = ["journal", "date", "name", "price", "closed", "account", "remark"]

    field_order = ["date", "account", "name", "price", "remark", "closed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.instance.debt_type = self.debt_type

        pin(self.fields["journal"], self.user.journal)

        self.translations()

    def translations(self):
        self.fields["date"].label = _("Date")
        self.fields["name"].label = _other_party_label(self.debt_type)
        self.fields["account"].label = _("Account")
        self.fields["price"].label = _("Sum")
        self.fields["remark"].label = _("Remark")
        self.fields["closed"].label = _("Returned")

    def clean(self):
        cleaned_data = super().clean()

        self._check_name_unique(cleaned_data)
        self._check_close(cleaned_data)
        self._check_price(cleaned_data)

        return cleaned_data

    def _check_name_unique(self, cleaned_data):
        name = cleaned_data.get("name")

        if cleaned_data.get("closed") or name == self.instance.name:
            return

        taken = DebtModelService(self.user, self.debt_type).items().filter(name=name)
        if taken.exists():
            self.add_error("name", _("The name must be unique."))

    def _check_close(self, cleaned_data):
        if not cleaned_data.get("closed"):
            return

        if not self.instance.pk:
            self.add_error("closed", CANT_CLOSE)
            return

        # an invalid price already has its field error and nothing to compare
        if "price" not in cleaned_data:
            return

        if self.instance.returned != cleaned_data["price"]:
            self.add_error("closed", CANT_CLOSE)

    def _check_price(self, cleaned_data):
        if not self.instance.pk or "price" not in cleaned_data:
            return

        if cleaned_data["price"] < self.instance.returned:
            self.add_error(
                "price", _("The debt can't be less than what has been returned.")
            )


class DebtReturnForm(DebtFormMixin, forms.ModelForm):
    price_fields = ("price",)
    price = CommaFloatField(min_value=0.01)

    class Meta:
        model = models.DebtReturn
        fields = ["date", "price", "remark", "account", "debt"]

    field_order = ["date", "account", "debt", "price", "remark"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.debt_field_settings()

        self.translations()

    def debt_field_settings(self):
        self.fields["debt"].queryset = DebtModelService(
            self.user, self.debt_type
        ).open_items()

    def translations(self):
        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("Account")
        self.fields["debt"].label = _other_party_label(self.debt_type)
        self.fields["price"].label = _("Sum")
        self.fields["remark"].label = _("Remark")

    def clean_price(self):
        price = self.cleaned_data["price"]
        debt = self.cleaned_data.get("debt")

        if not debt:
            return price

        returned = DebtReturnModelService(
            self.user, self.debt_type
        ).total_returned_for_debt(debt, leaving_out_pk=self.instance.pk or 0)

        # euros here: PriceToCentsFormMixin converts the field later, in clean()
        if float_to_int_cents(price) > debt.price - returned:
            msg = _("The amount due exceeds the debt.")
            raise ValidationError(msg)

        return price

    def clean(self):
        cleaned_data = super().clean()

        date = cleaned_data.get("date")
        debt = cleaned_data.get("debt")
        if debt and date and date < debt.date:
            self.add_error("date", _("The date preceding the debt's date."))

        return cleaned_data
