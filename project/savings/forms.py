from django import forms
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from ..accounts.forms import ACCOUNT_CLOSED
from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import PriceNeverEmptyFormMixin, PriceToCentsFormMixin
from ..core.lib.form_fields import CommaFloatField, date_field, pin
from ..core.lib.form_widgets import YearPickerWidget
from ..core.mixins.forms import (
    ClosedYearMixin,
    CloseNotBeforeRowsMixin,
    UserTodayMixin,
    YearBetweenMixin,
)
from .models import Saving, SavingType
from .services.model_services import SavingTypeModelService

FUND_CLOSED = gettext_lazy("Fund was closed in %(year)s.")


class SavingTypeForm(UserTodayMixin, CloseNotBeforeRowsMixin, forms.ModelForm):
    class Meta:
        model = SavingType
        fields = ["journal", "title", "type", "fee_source", "closed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._set_widgets()
        self._overwrite_default_queries()
        self._translate_fields()

    def _set_widgets(self):
        self.fields["closed"].widget = YearPickerWidget()

    def _overwrite_default_queries(self):
        pin(self.fields["journal"], self.user.journal)

    def _translate_fields(self):
        self.fields["title"].label = _("Fund")
        self.fields["closed"].label = _("Closed")
        self.fields["type"].label = _("Type")
        self.fields["fee_source"].label = _("Fee charged")

    def latest_row_year(self):
        return SavingTypeModelService(self.user).latest_row_year(self.instance)


class SavingForm(
    UserTodayMixin,
    ClosedYearMixin,
    PriceToCentsFormMixin,
    PriceNeverEmptyFormMixin,
    YearBetweenMixin,
    forms.ModelForm,
):
    closed_fields = {
        "saving_type": (FUND_CLOSED, "date"),
        "account": (ACCOUNT_CLOSED, "date"),
    }
    price_fields = ("price", "fee")
    price = CommaFloatField(min_value=0, required=False)
    fee = CommaFloatField(min_value=0, required=False)

    class Meta:
        model = Saving
        fields = ["date", "price", "fee", "remark", "saving_type", "account"]

    field_order = ["date", "account", "saving_type", "price", "fee", "remark"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._overwrite_default_queries()
        self._initial_fields_values()
        self._set_remark_rows()
        self._translate_fields()

    def _initial_fields_values(self):
        date_field(self.fields["date"], self.user, self.today)

        if account := self.fields["account"].queryset.first():
            self.fields["account"].initial = account

    def _set_remark_rows(self):
        self.fields["remark"].widget.attrs["rows"] = 3

    def _overwrite_default_queries(self):
        self.fields["saving_type"].queryset = SavingTypeModelService(self.user).items()
        self.fields["account"].queryset = AccountModelService(self.user).items()

    def _translate_fields(self):
        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("From account")
        self.fields["price"].label = _("Sum")
        self.fields["fee"].label = _("Fees")
        self.fields["remark"].label = _("Remark")
        self.fields["saving_type"].label = _("Fund")
