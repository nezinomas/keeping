from django import forms
from django.utils.translation import gettext as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import PriceToCentsFormMixin
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_fields import CommaFloatField, pin
from ..core.lib.form_widgets import DatePickerWidget
from ..core.mixins.forms import YearNotLaterMixin
from .models import Income, IncomeType
from .services.model_services import IncomeTypeModelService


class IncomeForm(PriceToCentsFormMixin, YearNotLaterMixin, forms.ModelForm):
    price_fields = ("price",)
    price = CommaFloatField(min_value=0.01)

    class Meta:
        model = Income
        fields = ("date", "price", "remark", "account", "income_type")

    field_order = ["date", "account", "income_type", "price", "remark"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.today = kwargs.pop("today")
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerWidget()

        self.fields["remark"].widget.attrs["rows"] = 3

        accounts = AccountModelService(self.user)
        incomes = IncomeTypeModelService(self.user)

        self.fields["account"].initial = accounts.items().first()
        self.fields["date"].initial = set_date_with_user_year(self.user, self.today)

        self.fields["income_type"].queryset = incomes.items()
        self.fields["account"].queryset = accounts.items()

        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("Account")
        self.fields["price"].label = _("Amount")
        self.fields["remark"].label = _("Remark")
        self.fields["income_type"].label = _("Incomes type")


class IncomeTypeForm(forms.ModelForm):
    class Meta:
        model = IncomeType
        fields = ["journal", "title", "type"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        kwargs.pop("today")
        super().__init__(*args, **kwargs)

        pin(self.fields["journal"], user.journal)

        self.fields["title"].label = _("Incomes type")
        self.fields["type"].label = _("Type")
