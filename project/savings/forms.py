from django import forms
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import PriceNeverEmptyFormMixin, PriceToCentsFormMixin
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_fields import CommaFloatField, pin
from ..core.lib.form_widgets import DatePickerWidget, YearPickerWidget
from ..core.mixins.forms import YearBetweenMixin
from .models import Saving, SavingType
from .services.model_services import SavingTypeModelService

FUND_CLOSED = gettext_lazy("Fund was closed in %(year)s.")


class SavingTypeForm(forms.ModelForm):
    class Meta:
        model = SavingType
        fields = ["journal", "title", "type", "fee_source", "closed"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        kwargs.pop("today")
        super().__init__(*args, **kwargs)

        self.fields["closed"].widget = YearPickerWidget()

        pin(self.fields["journal"], user.journal)

        self.fields["title"].label = _("Fund")
        self.fields["closed"].label = _("Closed")
        self.fields["type"].label = _("Type")
        self.fields["fee_source"].label = _("Fee charged")


class SavingForm(
    PriceToCentsFormMixin, PriceNeverEmptyFormMixin, YearBetweenMixin, forms.ModelForm
):
    price_fields = ("price", "fee")
    price = CommaFloatField(min_value=0, required=False)
    fee = CommaFloatField(min_value=0, required=False)

    class Meta:
        model = Saving
        fields = ["date", "price", "fee", "remark", "saving_type", "account"]

    field_order = ["date", "account", "saving_type", "price", "fee", "remark"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.today = kwargs.pop("today")
        super().__init__(*args, **kwargs)

        account_items = AccountModelService(self.user).items()

        self.fields["date"].widget = DatePickerWidget()

        self.fields["remark"].widget.attrs["rows"] = 3

        if account := account_items.first():
            self.fields["account"].initial = account
        self.fields["date"].initial = set_date_with_user_year(self.user, self.today)

        self.fields["saving_type"].queryset = SavingTypeModelService(self.user).items()
        self.fields["account"].queryset = account_items

        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("From account")
        self.fields["price"].label = _("Sum")
        self.fields["fee"].label = _("Fees")
        self.fields["remark"].label = _("Remark")
        self.fields["saving_type"].label = _("Fund")
