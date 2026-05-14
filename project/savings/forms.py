from django import forms
from django.utils.translation import gettext as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import ConvertPriceMixin
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_widgets import DatePickerWidget, YearPickerWidget
from ..core.mixins.forms import YearBetweenMixin
from .models import Saving, SavingType
from .services.model_services import SavingTypeModelService


class SavingTypeForm(forms.ModelForm):
    class Meta:
        model = SavingType
        fields = ["journal", "title", "type", "closed"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["closed"].widget = YearPickerWidget()

        # journal input
        self.fields["journal"].initial = user.journal
        self.fields["journal"].disabled = True
        self.fields["journal"].widget = forms.HiddenInput()

        self.fields["title"].label = _("Fund")
        self.fields["closed"].label = _("Closed")
        self.fields["type"].label = _("Type")


class SavingForm(ConvertPriceMixin, YearBetweenMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0, required=False)
    fee = forms.FloatField(min_value=0, required=False)

    class Meta:
        model = Saving
        fields = ["date", "price", "fee", "remark", "saving_type", "account"]

    field_order = ["date", "account", "saving_type", "price", "fee", "remark"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        account_items = AccountModelService(self.user).items()

        self.fields["date"].widget = DatePickerWidget()

        # form inputs settings
        self.fields["price"].widget.attrs = {"step": "0.01"}
        self.fields["fee"].widget.attrs = {"step": "0.01"}
        self.fields["remark"].widget.attrs["rows"] = 3

        # inital values
        self.fields["account"].initial = account_items.first()
        self.fields["date"].initial = set_date_with_user_year(self.user)

        # overwrite ForeignKey saving_type and account queryset
        self.fields["saving_type"].queryset = SavingTypeModelService(self.user).items()
        self.fields["account"].queryset = account_items

        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("From account")
        self.fields["price"].label = _("Sum")
        self.fields["fee"].label = _("Fees")
        self.fields["remark"].label = _("Remark")
        self.fields["saving_type"].label = _("Fund")

    def clean(self):
        cleaned_data = super().clean()

        fee = cleaned_data.get("fee")
        price = cleaned_data.get("price")

        if not price and not fee:
            _msg = _("The `Sum` and `Fee` fields cannot both be empty.")

            self.add_error("price", _msg)
            self.add_error("fee", _msg)

        return cleaned_data
