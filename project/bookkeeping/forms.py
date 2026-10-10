from collections.abc import Callable
from datetime import datetime, timezone

from django import forms
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.lib import date as core_date
from ..core.lib.convert_price import PriceToCentsFormMixin
from ..core.lib.form_fields import CommaFloatField, PreloadedModelChoiceField
from ..core.lib.form_widgets import DatePickerWidget
from ..expenses.services.model_services import ExpenseTypeModelService
from ..pensions.models import PensionType
from ..savings.models import SavingType
from .models import AccountWorth, PensionWorth, SavingWorth


def clean_date_and_closed(account: str, cleaned: dict, add_error: Callable) -> dict:
    dt = cleaned.get("date")
    if not dt:
        return cleaned

    account = cleaned.get(account)
    if not account or not account.closed:
        return cleaned

    if dt.year > account.closed:
        add_error(
            "date", _("Account was closed in %(year)s.") % ({"year": account.closed})
        )
    return cleaned


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


class SavingWorthForm(WorthForm):
    saving_type = PreloadedModelChoiceField(
        queryset=SavingType.objects.none(), label=""
    )
    field_order = ["date", "saving_type", "price"]

    class Meta(WorthForm.Meta):
        model = SavingWorth

    def clean(self):
        cleaned = super().clean()
        return clean_date_and_closed("saving_type", cleaned, self.add_error)


class AccountWorthForm(WorthForm):
    account = PreloadedModelChoiceField(queryset=Account.objects.none(), label="")
    field_order = ["date", "account", "price"]

    class Meta(WorthForm.Meta):
        model = AccountWorth

    def clean(self):
        cleaned = super().clean()
        return clean_date_and_closed("account", cleaned, self.add_error)


class PensionWorthForm(WorthForm):
    pension_type = PreloadedModelChoiceField(
        queryset=PensionType.objects.none(), label=""
    )
    field_order = ["date", "pension_type", "price"]

    class Meta(WorthForm.Meta):
        model = PensionWorth


class SummaryExpensesForm(forms.Form):
    types = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        choices = []
        for _type in ExpenseTypeModelService(self.user).objects:
            choices.append((_type.id, _type.title))

            choices.extend(
                (f"{_type.id}:{_name.id}", _name.title)
                for _name in _type.expensename_set.all()
            )

        self.fields["types"].choices = choices
        self.fields["types"].label = None

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("types"):
            return cleaned_data

        raise forms.ValidationError(_("At least one category has to be selected."))
