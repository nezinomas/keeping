from bootstrap_datepicker_plus.widgets import DatePickerInput, YearPickerInput
from django import forms
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.lib import date, form_utils, utils
from ..core.lib.convert_price import ConvertToPrice
from ..core.mixins.forms import YearBetweenMixin
from .models import Saving, SavingType


class SavingTypeForm(forms.ModelForm):
    class Meta:
        model = SavingType
        fields = ["journal", "title", "type", "closed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["closed"].widget = YearPickerInput(
            options={
                "locale": utils.get_user().journal.lang,
            }
        )

        # journal input
        self.fields["journal"].initial = utils.get_user().journal
        self.fields["journal"].disabled = True
        self.fields["journal"].widget = forms.HiddenInput()

        self.fields["title"].label = _("Fund")
        self.fields["closed"].label = _("Closed")
        self.fields["type"].label = _("Type")

    def clean(self):
        cleaned_data = super().clean()
        form_utils.clean_year_picker_input(
            "closed", self.data, cleaned_data, self.errors
        )

        return cleaned_data


class SavingForm(ConvertToPrice, YearBetweenMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0, required=False)
    fee = forms.FloatField(min_value=0, required=False)

    class Meta:
        model = Saving
        fields = ["date", "price", "fee", "remark", "saving_type", "account"]

    field_order = ["date", "account", "saving_type", "price", "fee", "remark"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerInput(
            options={
                "locale": utils.get_user().journal.lang,
            }
        )

        # form inputs settings
        self.fields["price"].widget.attrs = {"step": "0.01"}
        self.fields["fee"].widget.attrs = {"step": "0.01"}
        self.fields["remark"].widget.attrs["rows"] = 3

        # inital values
        self.fields["account"].initial = Account.objects.items().first()
        self.fields["date"].initial = date.set_year_for_form()

        # overwrite ForeignKey saving_type and account queryset
        self.fields["saving_type"].queryset = SavingType.objects.items()
        self.fields["account"].queryset = Account.objects.items()

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
