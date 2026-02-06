from datetime import datetime

from django import forms
from django.utils.translation import gettext as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import ConvertToPriceMixin
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_widgets import DatePickerWidget
from ..incomes.services.model_services import IncomeTypeModelService
from .models import Income, IncomeType


class IncomeForm(ConvertToPriceMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0.01)

    class Meta:
        model = Income
        fields = ("date", "price", "remark", "account", "income_type")

    field_order = ["date", "account", "income_type", "price", "remark"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerWidget()

        # form inputs settings
        self.fields["remark"].widget.attrs["rows"] = 3

        accounts = AccountModelService(self.user)
        incomes = IncomeTypeModelService(self.user)

        # inital values
        self.fields["account"].initial = accounts.items().first()
        self.fields["date"].initial = set_date_with_user_year(self.user)

        # overwrite ForeignKey expense_type queryset
        self.fields["income_type"].queryset = incomes.items()
        self.fields["account"].queryset = accounts.items()

        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("Account")
        self.fields["price"].label = _("Amount")
        self.fields["remark"].label = _("Remark")
        self.fields["income_type"].label = _("Incomes type")

    def clean_date(self):
        dt = self.cleaned_data["date"]

        year_user = self.user.year
        year_instance = dt.year
        year_now = datetime.now().year

        diff = 1
        if (year_instance - year_now) > diff:
            year_msg = year_user + diff
            self.add_error(
                "date",
                _("Year cannot be greater than %(year)s") % ({"year": year_msg}),
            )

        return dt


class IncomeTypeForm(forms.ModelForm):
    class Meta:
        model = IncomeType
        fields = ["journal", "title", "type"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # user input
        self.fields["journal"].initial = user.journal
        self.fields["journal"].disabled = True
        self.fields["journal"].widget = forms.HiddenInput()

        self.fields["title"].label = _("Incomes type")
        self.fields["type"].label = _("Type")
