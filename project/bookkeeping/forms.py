from datetime import datetime, timezone

from django import forms
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from ..accounts.models import Account
from ..core.lib import date as core_date
from ..core.lib.convert_price import PriceToCentsFormMixin
from ..core.lib.form_fields import CommaFloatField, PreloadedModelChoiceField
from ..core.lib.form_widgets import DatePickerWidget
from ..expenses.services.model_services import ExpenseTypeModelService
from ..pensions.models import PensionType
from ..savings.models import SavingType
from .models import AccountWorth, PensionWorth, SavingWorth


class DateFieldMixin:
    def clean_date(self):
        dt = self.cleaned_data["date"]
        now = datetime.now()
        return datetime(
            dt.year,
            dt.month,
            dt.day,
            now.hour,
            now.minute,
            now.second,
            tzinfo=timezone.utc,
        )


class WorthForm(PriceToCentsFormMixin, DateFieldMixin, forms.ModelForm):
    # the fund field is declared, not in Meta.fields: model validation would
    # query it once per form; the formset hands every form the same funds
    price_fields = ("price",)
    price = CommaFloatField(min_value=0, required=False, label="")

    class Meta:
        fields = ["date", "price"]
        labels = {"date": ""}

    def __init__(self, *args, user, funds, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerWidget()
        self.fields["date"].initial = core_date.set_date_with_user_year(user)
        self.fields[self.fund_field].preload(funds)

    @property
    def fund_field(self):
        return self._meta.model.fund_field

    def clean(self):
        cleaned = super().clean()
        if fund := cleaned.get(self.fund_field):
            setattr(self.instance, self.fund_field, fund)
        return cleaned


class ClosedFundMixin:
    def clean(self):
        cleaned = super().clean()
        dt = cleaned.get("date")
        fund = cleaned.get(self.fund_field)
        if not dt or not fund or not fund.closed:
            return cleaned

        if dt.year > fund.closed:
            self.add_error("date", self.closed_message % {"year": fund.closed})
        return cleaned


class SavingWorthForm(ClosedFundMixin, WorthForm):
    closed_message = gettext_lazy("Fund was closed in %(year)s.")
    duplicate_message = gettext_lazy("The same funds are selected.")
    saving_type = PreloadedModelChoiceField(
        queryset=SavingType.objects.none(), label=""
    )
    field_order = ["date", "saving_type", "price"]

    class Meta(WorthForm.Meta):
        model = SavingWorth


class AccountWorthForm(ClosedFundMixin, WorthForm):
    closed_message = gettext_lazy("Account was closed in %(year)s.")
    duplicate_message = gettext_lazy("The same accounts are selected.")
    account = PreloadedModelChoiceField(queryset=Account.objects.none(), label="")
    field_order = ["date", "account", "price"]

    class Meta(WorthForm.Meta):
        model = AccountWorth


class PensionWorthForm(WorthForm):
    duplicate_message = gettext_lazy("The same pensions are selected.")
    pension_type = PreloadedModelChoiceField(
        queryset=PensionType.objects.none(), label=""
    )
    field_order = ["date", "pension_type", "price"]

    class Meta(WorthForm.Meta):
        model = PensionWorth


class SummaryExpensesForm(forms.Form):
    types = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []
        for _type in ExpenseTypeModelService(user).objects:
            choices.append((_type.id, _type.title))

            choices.extend(
                (f"{_type.id}:{_name.id}", _name.title)
                for _name in _type.expensename_set.all()
            )

        self.fields["types"].choices = choices

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("types"):
            return cleaned_data

        raise forms.ValidationError(_("At least one category has to be selected."))
