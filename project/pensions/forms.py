from django import forms
from django.utils.translation import gettext as _

from ..core.lib.convert_price import PriceNeverEmptyFormMixin, PriceToCentsFormMixin
from ..core.lib.form_fields import CommaFloatField, date_field, pin
from ..core.mixins.forms import UserTodayMixin, YearBetweenMixin
from .models import Pension, PensionType
from .services.model_services import PensionTypeModelService


class PensionForm(
    UserTodayMixin,
    PriceToCentsFormMixin,
    PriceNeverEmptyFormMixin,
    YearBetweenMixin,
    forms.ModelForm,
):
    price_fields = ("price", "fee")
    price = CommaFloatField(required=False, min_value=0)
    fee = CommaFloatField(required=False, min_value=0)

    class Meta:
        model = Pension
        fields = ["date", "price", "fee", "remark", "pension_type"]

    field_order = ["date", "pension_type", "price", "fee", "remark"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        date_field(self.fields["date"], self.user, self.today)

        self.fields["remark"].widget.attrs["rows"] = 3

        self.fields["pension_type"].queryset = PensionTypeModelService(
            self.user
        ).items()

        self.fields["date"].label = _("Date")
        self.fields["price"].label = _("Sum")
        self.fields["fee"].label = _("Fee")
        self.fields["remark"].label = _("Remark")
        self.fields["pension_type"].label = _("Fund")


class PensionTypeForm(UserTodayMixin, forms.ModelForm):
    class Meta:
        model = PensionType
        fields = ["journal", "title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pin(self.fields["journal"], self.user.journal)

        self.fields["title"].label = _("Fund title")
