from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import ConvertPriceMixin
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_fields import CommaFloatField
from ..core.lib.form_widgets import DatePickerWidget
from ..core.mixins.forms import YearBetweenMixin
from ..savings.services.model_services import (
    SavingTypeModelService,
)
from .models import SavingChange, SavingClose, SavingType, Transaction


class TransactionForm(ConvertPriceMixin, YearBetweenMixin, forms.ModelForm):
    price = CommaFloatField(min_value=0.01)

    class Meta:
        model = Transaction
        fields = ["date", "from_account", "to_account", "price"]

    field_order = ["date", "from_account", "to_account", "price"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()

        self.fields["price"].label = _("Amount")
        self.fields["date"].initial = set_date_with_user_year(self.user)

    def _overwrite_default_queries(self):
        account = AccountModelService(self.user)

        from_account = self.fields["from_account"]
        to_account = self.fields["to_account"]

        from_account.queryset = account.items()
        to_account.queryset = account.none()

        _from = getattr(self.instance, "from_account", None)
        _from_pk = getattr(_from, "pk", None)
        if from_account_pk := self.data.get("from_account") or _from_pk:
            to_account.queryset = account.items().exclude(pk=from_account_pk)

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

    def _sync_from_account_close(self):
        fund = SavingType.objects.get(pk=self.instance.from_account.pk)
        closed = self._close_year(fund.closed)
        if fund.closed == closed:
            return  # a type save re-syncs savings; skip it when nothing changed

        fund.closed = closed
        fund.save()

    def _close_year(self, current):
        if not self.cleaned_data.get("close"):
            return None

        year = self.instance.date.year
        if current is None or year > current or self._closed_the_fund(current):
            return year

        # the box comes ticked on every row of a closed fund; an earlier row keeps it
        return current

    def _closed_the_fund(self, current) -> bool:
        return bool(self.instance.pk) and self.initial["date"].year == current


class SavingCloseForm(
    CloseFromAccountMixin, ConvertPriceMixin, YearBetweenMixin, forms.ModelForm
):
    price = CommaFloatField(min_value=0.01)
    fee = CommaFloatField(min_value=0.01, required=False)
    close = forms.BooleanField(required=False)

    class Meta:
        model = SavingClose
        fields = ["date", "from_account", "to_account", "price", "fee", "close"]

    field_order = ["date", "from_account", "to_account", "price", "fee", "close"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._translate_fields()

        # if from_account is closed, update close checkbox value
        if hasattr(self.instance, "from_account") and self.instance.from_account.closed:
            self.fields["close"].initial = True

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()
        self.fields["date"].initial = set_date_with_user_year(self.user)

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
        self.fields["close"].label = mark_safe(
            f"{_('Close')} <b>{_('From account')}</b>"
        )

    def save(self, *args, **kwargs):
        self._sync_from_account_close()
        return super().save(*args, **kwargs)


class SavingChangeForm(
    CloseFromAccountMixin, ConvertPriceMixin, YearBetweenMixin, forms.ModelForm
):
    price = CommaFloatField(min_value=0.01)
    fee = CommaFloatField(min_value=0.01, required=False)
    close = forms.BooleanField(required=False)

    class Meta:
        model = SavingChange
        fields = ["date", "from_account", "to_account", "price", "fee", "close"]

    field_order = ["date", "from_account", "to_account", "price", "fee", "close"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_default_queries()
        self._set_htmx_attributes()
        self._translate_fields()

        # if from_account is closed, update close checkbox value
        if hasattr(self.instance, "from_account") and self.instance.from_account.closed:
            self.fields["close"].initial = True

    def _initial_fields_values(self):
        self.fields["date"].widget = DatePickerWidget()

        # initial values
        self.fields["date"].initial = set_date_with_user_year(self.user)

    def _overwrite_default_queries(self):
        from_account = self.fields["from_account"]
        to_account = self.fields["to_account"]

        saving_model = SavingTypeModelService(self.user)

        from_account.queryset = saving_model.items()
        to_account.queryset = saving_model.none()

        _from = getattr(self.instance, "from_account", None)
        _from_pk = getattr(_from, "pk", None)
        if from_account_pk := self.data.get("from_account") or _from_pk:
            to_account.queryset = saving_model.items().exclude(pk=from_account_pk)

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
        self.fields["close"].label = mark_safe(
            f"{_('Close')} <b>{_('From account')}</b>"
        )

    def save(self, *args, **kwargs):
        self._sync_from_account_close()
        return super().save(*args, **kwargs)
