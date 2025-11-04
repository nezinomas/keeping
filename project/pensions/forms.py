from datetime import datetime

from django import forms
from django.utils.translation import gettext as _

from ..core.lib.convert_price import ConvertToPrice
from ..core.lib.form_widgets import DatePickerWidget
from ..core.mixins.forms import YearBetweenMixin
from .models import Pension, PensionType


class PensionForm(ConvertToPrice, YearBetweenMixin, forms.ModelForm):
    price = forms.FloatField(required=False, min_value=0)
    fee = forms.FloatField(required=False, min_value=0)

    class Meta:
        model = Pension
        fields = ["date", "price", "fee", "remark", "pension_type"]

    field_order = ["date", "pension_type", "price", "fee", "remark"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerWidget()

        # form inputs settings
        self.fields["remark"].widget.attrs["rows"] = 3

        # inital values
        self.fields["date"].initial = datetime.now()

        # overwrite ForeignKey saving_type queryset
        self.fields["pension_type"].queryset = PensionType.objects.items()

        self.fields["date"].label = _("Date")
        self.fields["price"].label = _("Sum")
        self.fields["fee"].label = _("Fee")
        self.fields["remark"].label = _("Remark")
        self.fields["pension_type"].label = _("Fund")

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        fee = cleaned_data.get("fee")

        if not price and not fee:
            _msg = _("The `Sum` and `Fee` fields cannot both be empty.")

            self.add_error("price", _msg)
            self.add_error("fee", _msg)

        return cleaned_data


class PensionTypeForm(forms.ModelForm):
    class Meta:
        model = PensionType
        fields = ["journal", "title"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # journal input
        self.fields["journal"].initial = user.journal
        self.fields["journal"].disabled = True
        self.fields["journal"].widget = forms.HiddenInput()

        self.fields["title"].label = _("Fund title")
