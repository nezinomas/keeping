from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _

from ..accounts.forms import ACCOUNT_CLOSED
from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import NeverEmptyFormMixin, PriceToCentsFormMixin
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_fields import CommaFloatField
from ..core.lib.form_widgets import DatePickerWidget
from ..core.lib.utils import int_or_zero
from ..core.mixins.forms import ClosedYearMixin, YearBetweenMixin
from ..savings.forms import FUND_CLOSED
from ..savings.services.model_services import SavingTypeModelService
from .close_rules import CloseBox
from .models import SavingChange, SavingClose, Transaction
from .services.close_year import FundCloseYear


def set_to_account_choices(form, service):
    """Every item of the service but the move's from_account."""
    to_account = form.fields["to_account"]
    to_account.queryset = service.none()

    if from_account_pk := (
        int_or_zero(form.data.get("from_account")) or form.instance.from_account_id
    ):
        to_account.queryset = service.items().exclude(pk=from_account_pk)


class TransactionForm(
    ClosedYearMixin, PriceToCentsFormMixin, YearBetweenMixin, forms.ModelForm
):
    closed_fields = {
        "from_account": (ACCOUNT_CLOSED, "date"),
        "to_account": (ACCOUNT_CLOSED, "date"),
    }
    price_fields = ("price",)
    price = CommaFloatField(min_value=0.01)

    class Meta:
        model = Transaction
        fields = ["date", "from_account", "to_account", "price"]

    field_order = ["date", "from_account", "to_account", "price"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.today = kwargs.pop("today")
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()

        self.fields["price"].label = _("Amount")
        self.fields["date"].initial = set_date_with_user_year(self.user, self.today)

    def _overwrite_default_queries(self):
        account = AccountModelService(self.user)

        self.fields["from_account"].queryset = account.items()
        set_to_account_choices(self, account)

    def _set_htmx_attributes(self):
        url = reverse("accounts:load")

        field = self.fields["from_account"]
        field.widget.attrs["hx-get"] = url
        field.widget.attrs["hx-target"] = "#id_to_account"
        field.widget.attrs["hx-trigger"] = "change"

    def _translate_fields(self):
        self.fields["date"].label = _("Date")
        self.fields["from_account"].label = _("From account")
        self.fields["to_account"].label = _("To account")


class CloseFromAccountMixin:
    """Closes or reopens the from-fund with the form's `close` checkbox."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["close"].label = render_to_string(
            "transactions/includes/close_label.html"
        )
        if self.instance.pk:
            self.fields["close"].initial = FundCloseYear.is_closing_move(
                self.instance.from_account_id, self.instance.date
            )

    def save(self, *args, **kwargs):
        ticked = self.cleaned_data["close"]
        changed = "close" in self.changed_data
        # the box was rendered for the fund it left: on the new one only a tick speaks
        if "from_account" in self.changed_data:
            changed = ticked
        self.instance.close_rule = CloseBox(changed, ticked)

        return super().save(*args, **kwargs)


class SavingCloseForm(
    ClosedYearMixin,
    NeverEmptyFormMixin,
    CloseFromAccountMixin,
    PriceToCentsFormMixin,
    YearBetweenMixin,
    forms.ModelForm,
):
    closed_fields = {
        "from_account": (FUND_CLOSED, "date"),
        "to_account": (ACCOUNT_CLOSED, "date"),
    }
    price_fields = ("price", "fee")
    _never_empty = ("fee",)

    price = CommaFloatField(min_value=0.01)
    fee = CommaFloatField(min_value=0.01, required=False)
    close = forms.BooleanField(required=False)

    class Meta:
        model = SavingClose
        fields = ["date", "from_account", "to_account", "price", "fee", "close"]

    field_order = ["date", "from_account", "to_account", "price", "fee", "close"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.today = kwargs.pop("today")
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._translate_fields()

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()
        self.fields["date"].initial = set_date_with_user_year(self.user, self.today)

    def _overwrite_default_queries(self):
        self.fields["from_account"].queryset = SavingTypeModelService(self.user).items()
        self.fields["to_account"].queryset = AccountModelService(self.user).items()

    def _translate_fields(self):
        self.fields["price"].label = _("Amount")
        self.fields["price"].help_text = _("Amount left after fee")
        self.fields["fee"].label = _("Fees")
        self.fields["date"].label = _("Date")
        self.fields["from_account"].label = _("From account")
        self.fields["to_account"].label = _("To account")


class SavingChangeForm(
    ClosedYearMixin,
    NeverEmptyFormMixin,
    CloseFromAccountMixin,
    PriceToCentsFormMixin,
    YearBetweenMixin,
    forms.ModelForm,
):
    closed_fields = {
        "from_account": (FUND_CLOSED, "date"),
        "to_account": (FUND_CLOSED, "to_account"),
    }
    price_fields = ("price", "fee")
    _never_empty = ("fee",)

    price = CommaFloatField(min_value=0.01)
    fee = CommaFloatField(min_value=0.01, required=False)
    close = forms.BooleanField(required=False)

    class Meta:
        model = SavingChange
        fields = ["date", "from_account", "to_account", "price", "fee", "close"]

    field_order = ["date", "from_account", "to_account", "price", "fee", "close"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.today = kwargs.pop("today")
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()

        self.fields["date"].initial = set_date_with_user_year(self.user, self.today)

    def _overwrite_default_queries(self):
        saving_model = SavingTypeModelService(self.user)

        self.fields["from_account"].queryset = saving_model.items()
        set_to_account_choices(self, saving_model)

    def _set_htmx_attributes(self):
        url = reverse("transactions:load_saving_type")

        field = self.fields["from_account"]
        field.widget.attrs["hx-get"] = url
        field.widget.attrs["hx-target"] = "#id_to_account"
        field.widget.attrs["hx-trigger"] = "change"

    def _translate_fields(self):
        self.fields["price"].label = _("Amount")
        self.fields["price"].help_text = _("Amount left after fee")
        self.fields["fee"].label = _("Fees")
        self.fields["date"].label = _("Date")
        self.fields["from_account"].label = _("From account")
        self.fields["to_account"].label = _("To account")
