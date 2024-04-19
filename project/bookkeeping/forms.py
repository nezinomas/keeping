from datetime import datetime, timezone
from typing import Callable

from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.lib import date as core_date
from ..core.lib import utils
from ..core.lib.convert_price import ConvertToPrice
from ..expenses.models import ExpenseType
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


class SavingWorthForm(ConvertToPrice, DateFieldMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0, required=False)

    class Meta:
        model = SavingWorth
        fields = ["date", "saving_type", "price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerInput(
            options={
                "locale": utils.get_user().journal.lang,
            }
        )
        self.fields["date"].initial = core_date.set_year_for_form()

        # overwrite FK
        self.fields["saving_type"].queryset = SavingType.objects.items()

        self.helper = FormHelper()
        self.helper.form_show_labels = False

    def clean(self):
        cleaned = super().clean()
        return clean_date_and_closed("saving_type", cleaned, self.add_error)


class AccountWorthForm(ConvertToPrice, DateFieldMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0, required=False)

    class Meta:
        model = AccountWorth
        fields = ["date", "account", "price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerInput(
            options={
                "locale": utils.get_user().journal.lang,
            }
        )
        self.fields["date"].initial = core_date.set_year_for_form()

        # overwrite FK
        self.fields["account"].queryset = Account.objects.items()

        self.helper = FormHelper()
        self.helper.form_show_labels = False

    def clean(self):
        cleaned = super().clean()
        return clean_date_and_closed("account", cleaned, self.add_error)


class PensionWorthForm(ConvertToPrice, DateFieldMixin, forms.ModelForm):
    price = forms.FloatField(min_value=0, required=False)

    class Meta:
        model = PensionWorth
        fields = ["date", "pension_type", "price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].widget = DatePickerInput(
            options={
                "locale": utils.get_user().journal.lang,
            }
        )
        self.fields["date"].initial = core_date.set_year_for_form()

        # overwrite FK
        self.fields["pension_type"].queryset = PensionType.objects.items()

        self.helper = FormHelper()
        self.helper.form_show_labels = False


class SummaryExpensesForm(forms.Form):
    types = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []
        for _type in ExpenseType.objects.items():
            choices.append((_type.id, _type.title))

            choices.extend(
                (f"{_type.id}:{_name.id}", _name.title)
                for _name in _type.expensename_set.all()
            )

        self.fields["types"].choices = choices
        self.fields["types"].label = None

        self.helper = FormHelper()
        self.helper.form_show_labels = False

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("types"):
            return cleaned_data

        raise forms.ValidationError(_("At least one category has to be selected."))
