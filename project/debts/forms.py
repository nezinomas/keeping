from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import PriceToCentsFormMixin, float_to_int_cents
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_fields import CommaFloatField, pin
from ..core.lib.form_widgets import DatePickerWidget
from ..core.mixins.forms import YearBetweenMixin
from . import models
from .services.model_services import DebtModelService, DebtReturnModelService


def _other_party_label(debt_type):
    return {
        models.Debt.DebtType.LEND: _("Borrower"),
        models.Debt.DebtType.BORROW: _("Lender"),
    }[debt_type]


class DebtFormMixin(PriceToCentsFormMixin, YearBetweenMixin):
    """The date, account and remark every debt form sets up the same way."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.debt_type = kwargs.pop("debt_type")

        super().__init__(*args, **kwargs)

        self.fields["remark"].widget.attrs["rows"] = 3

        self.date_field_settings()
        self.account_field_settings()

    def date_field_settings(self):
        self.fields["date"].widget = DatePickerWidget()
        self.fields["date"].initial = set_date_with_user_year(self.user, date.today())

    def account_field_settings(self):
        accounts = AccountModelService(self.user).items()

        self.fields["account"].initial = accounts.first()
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

        name = cleaned_data.get("name")
        closed = cleaned_data.get("closed")
        price = cleaned_data.get("price")

        if (
            not closed
            and name != self.instance.name
            and DebtModelService(self.user, self.debt_type)
            .items()
            .filter(name=name)
            .exists()
        ):
            self.add_error("name", _("The name must be unique."))

        _msg_cant_close = _("You can't close a debt that hasn't been returned.")
        if not self.instance.pk and closed:
            self.add_error("closed", _msg_cant_close)

        # an invalid price already has its field error and nothing to compare
        if "price" not in cleaned_data:
            return cleaned_data

        if self.instance.pk and closed and self.instance.returned != price:
            self.add_error("closed", _msg_cant_close)

        if self.instance.pk and price < self.instance.returned:
            self.add_error(
                "price", _("The debt can't be less than what has been returned.")
            )

        return cleaned_data


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
