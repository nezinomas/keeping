from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _

from ..accounts.forms import ACCOUNT_CLOSED
from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import NeverEmptyFormMixin, PriceToCentsFormMixin
from ..core.lib.form_fields import CommaFloatField, date_field
from ..core.lib.utils import int_or_zero
from ..core.mixins.forms import ClosedYearMixin, UserTodayMixin, YearBetweenMixin
from ..savings.forms import FUND_CLOSED
from ..savings.services.model_services import SavingTypeModelService
from .close_rules import CLOSE, KEEP, REOPEN, CloseRule
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


def from_account_loads(form, url):
    """The from_account's change reloads the to_account's options from `url`."""
    attrs = form.fields["from_account"].widget.attrs
    attrs["hx-get"] = url
    attrs["hx-target"] = "#id_to_account"
    attrs["hx-trigger"] = "change"


class MoveFieldsMixin(UserTodayMixin):
    """The date, from_account and to_account every move form shares."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._set_move_fields()

    def _set_move_fields(self):
        date_field(self.fields["date"], self.user, self.today)
        self.fields["date"].label = _("Date")
        self.fields["from_account"].label = _("From account")
        self.fields["to_account"].label = _("To account")


class TransactionForm(
    MoveFieldsMixin,
    ClosedYearMixin,
    PriceToCentsFormMixin,
    YearBetweenMixin,
    forms.ModelForm,
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
        super().__init__(*args, **kwargs)

        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()

    def _overwrite_default_queries(self):
        account = AccountModelService(self.user)

        self.fields["from_account"].queryset = account.items()
        set_to_account_choices(self, account)

    def _set_htmx_attributes(self):
        from_account_loads(self, reverse("accounts:load"))

    def _translate_fields(self):
        self.fields["price"].label = _("Amount")


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
        self.instance.close_rule = self._close_rule()

        return super().save(*args, **kwargs)

    def _close_rule(self) -> CloseRule:
        # the box was rendered for the fund it left: on the new one only a tick speaks
        moved = "from_account" in self.changed_data
        box_changed = "close" in self.changed_data

        if self.cleaned_data["close"] and (moved or box_changed):
            return CLOSE

        if moved or not box_changed:
            return KEEP

        return REOPEN


class SavingCloseForm(
    MoveFieldsMixin,
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
        super().__init__(*args, **kwargs)

        self._overwrite_default_queries()
        self._translate_fields()

    def _overwrite_default_queries(self):
        self.fields["from_account"].queryset = SavingTypeModelService(self.user).items()
        self.fields["to_account"].queryset = AccountModelService(self.user).items()

    def _translate_fields(self):
        self.fields["price"].label = _("Amount")
        self.fields["price"].help_text = _("Amount left after fee")
        self.fields["fee"].label = _("Fees")


class SavingChangeForm(
    MoveFieldsMixin,
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
        super().__init__(*args, **kwargs)

        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()

    def _overwrite_default_queries(self):
        saving_model = SavingTypeModelService(self.user)

        self.fields["from_account"].queryset = saving_model.items()
        set_to_account_choices(self, saving_model)

    def _set_htmx_attributes(self):
        from_account_loads(self, reverse("transactions:load_saving_type"))

    def _translate_fields(self):
        self.fields["price"].label = _("Amount")
        self.fields["price"].help_text = _("Amount left after fee")
        self.fields["fee"].label = _("Fees")
