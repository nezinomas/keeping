from datetime import datetime, timezone

from django import forms
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from ..accounts.models import Account
from ..core.lib.convert_price import PriceToCentsFormMixin
from ..core.lib.form_fields import (
    CommaFloatField,
    PreloadedModelChoiceField,
    date_field,
)
from ..core.mixins.forms import ClosedYearMixin, UserTodayMixin
from ..expenses.services.model_services import ExpenseTypeModelService
from ..pensions.models import PensionType
from ..savings.forms import FUND_CLOSED
from ..savings.models import SavingType
from .models import AccountWorth, PensionWorth, SavingWorth


class WorthForm(UserTodayMixin, PriceToCentsFormMixin, forms.ModelForm):
    # the fund field is declared, not in Meta.fields: model validation would
    # query it once per form; the formset hands every form the same funds
    price_fields = ("price",)
    price = CommaFloatField(min_value=0, required=False, label="")

    class Meta:
        fields = ["date", "price"]
        labels = {"date": ""}

    def __init__(self, *args, funds, now, **kwargs):
        super().__init__(*args, **kwargs)
        self.now = now

        date_field(self.fields["date"], self.user, self.today)
        self.fields[self.fund_field].preload(funds)

    @property
    def fund_field(self):
        return self._meta.model.fund_field

    def clean_date(self):
        return datetime.combine(
            self.cleaned_data["date"],
            self.now.time().replace(microsecond=0),
            tzinfo=timezone.utc,
        )

    def clean(self):
        cleaned = super().clean()
        if fund := cleaned.get(self.fund_field):
            setattr(self.instance, self.fund_field, fund)
        return cleaned


class SavingWorthForm(ClosedYearMixin, WorthForm):
    closed_fields = {"saving_type": (FUND_CLOSED, "date")}
    duplicate_message = gettext_lazy("The same funds are selected.")
    saving_type = PreloadedModelChoiceField(
        queryset=SavingType.objects.none(), label=""
    )
    field_order = ["date", "saving_type", "price"]

    class Meta(WorthForm.Meta):
        model = SavingWorth


class AccountWorthForm(ClosedYearMixin, WorthForm):
    closed_fields = {
        "account": (gettext_lazy("Account was closed in %(year)s."), "date")
    }
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


class SummaryExpensesForm(UserTodayMixin, forms.Form):
    types = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []
        for expense_type in ExpenseTypeModelService(self.user).objects:
            choices.append((expense_type.id, expense_type.title))

            choices.extend(
                (f"{expense_type.id}:{name.id}", name.title)
                for name in expense_type.expensename_set.all()
            )

        self.fields["types"].choices = choices

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("types"):
            return cleaned_data

        raise forms.ValidationError(_("At least one category has to be selected."))
