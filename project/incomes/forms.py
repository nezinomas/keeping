from django import forms
from django.utils.translation import gettext as _

from ..accounts.forms import ACCOUNT_CLOSED
from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import PriceToCentsFormMixin
from ..core.lib.form_fields import CommaFloatField, date_field, pin
from ..core.mixins.forms import ClosedYearMixin, UserTodayMixin, YearNotLaterMixin
from .models import Income, IncomeType
from .services.model_services import IncomeTypeModelService


class IncomeForm(
    UserTodayMixin,
    ClosedYearMixin,
    PriceToCentsFormMixin,
    YearNotLaterMixin,
    forms.ModelForm,
):
    closed_fields = {"account": (ACCOUNT_CLOSED, "date")}
    price_fields = ("price",)
    price = CommaFloatField(min_value=0.01)

    class Meta:
        model = Income
        fields = ("date", "price", "remark", "account", "income_type")

    field_order = ["date", "account", "income_type", "price", "remark"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._overwrite_default_queries()
        self._initial_fields_values()
        self._translate_fields()
        self._set_widgets()

    def _initial_fields_values(self):
        date_field(self.fields["date"], self.user, self.today)

        if account := self.fields["account"].queryset.first():
            self.fields["account"].initial = account

    def _overwrite_default_queries(self):
        self.fields["account"].queryset = AccountModelService(self.user).items()
        self.fields["income_type"].queryset = IncomeTypeModelService(self.user).items()

    def _translate_fields(self):
        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("Account")
        self.fields["price"].label = _("Amount")
        self.fields["remark"].label = _("Remark")
        self.fields["income_type"].label = _("Incomes type")

    def _set_widgets(self):
        self.fields["remark"].widget.attrs["rows"] = 3


class IncomeTypeForm(UserTodayMixin, forms.ModelForm):
    class Meta:
        model = IncomeType
        fields = ["journal", "title", "type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pin(self.fields["journal"], self.user.journal)

        self.fields["title"].label = _("Incomes type")
        self.fields["type"].label = _("Type")
