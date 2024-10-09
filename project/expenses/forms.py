import contextlib
from datetime import datetime

from bootstrap_datepicker_plus.widgets import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.lib import form_utils, utils
from ..core.lib.convert_price import ConvertToPrice
from ..core.lib.date import set_year_for_form
from .models import Expense, ExpenseName, ExpenseType


class ExpenseForm(ConvertToPrice, forms.ModelForm):
    price = forms.FloatField(min_value=0.01)
    total_sum = forms.CharField(required=False)

    class Meta:
        model = Expense
        fields = (
            "date",
            "price",
            "quantity",
            "expense_type",
            "expense_name",
            "remark",
            "exception",
            "account",
            "attachment",
        )

    field_order = [
        "date",
        "account",
        "expense_type",
        "expense_name",
        "total_sum",
        "quantity",
        "remark",
        "price",
        "attachment",
        "exception",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = utils.get_user()

        self._initial_fields_values()
        self._overwrite_account_query()
        self._overwrite_expense_type_query()
        self._overwrite_expense_name_query(user)
        self._set_htmx_attributes()
        self._translate_fields()

        # form inputs settings
        self.fields["date"].widget = DatePickerInput(
            options={
                "locale": user.journal.lang,
            }
        )
        self.fields["price"].widget.attrs = {
            "readonly": True,
            "class": "disabled",
        }
        self.fields["remark"].widget.attrs["rows"] = 3

        self.helper = FormHelper()

    def _initial_fields_values(self):
        if not self.instance.pk:
            self.fields["date"].initial = set_year_for_form()
            self.fields["account"].initial = Account.objects.items().first()
            self.fields["price"].initial = "0.00"

    def _overwrite_account_query(self):
        if self.instance.pk:
            qs = Account.objects.items(year=self.instance.date.year)
        else:
            qs = Account.objects.items()

        self.fields["account"].queryset = qs

    def _overwrite_expense_type_query(self):
        self.fields["expense_type"].queryset = ExpenseType.objects.items()

    def _overwrite_expense_name_query(self, user):
        expense_type_pk = None
        with contextlib.suppress(TypeError, ValueError):
            expense_type_pk = int(self.data.get("expense_type"))

        if expense_type_pk is None and self.instance.pk:
            expense_type_pk = self.instance.expense_type.pk

        if expense_type_pk:
            qs = (
                ExpenseName.objects.related()
                .filter(parent=expense_type_pk)
                .year(user.year)
            )
        else:
            qs = ExpenseName.objects.none()

        self.fields["expense_name"].queryset = qs

    def _set_htmx_attributes(self):
        url = reverse("expenses:load_expense_name")

        expense_type = self.fields["expense_type"]
        expense_type.widget.attrs["hx-get"] = url
        expense_type.widget.attrs["hx-target"] = "#id_expense_name"
        expense_type.widget.attrs["hx-trigger"] = "change"

    def _translate_fields(self):
        self.fields["date"].label = _("Date")
        self.fields["price"].label = _("Full price")
        self.fields["quantity"].label = _("How many")
        self.fields["expense_type"].label = _("Expense type")
        self.fields["expense_name"].label = _("Expense name")
        self.fields["remark"].label = _("Remark")
        self.fields["exception"].label = _("Exception")
        self.fields["account"].label = _("Account")
        self.fields["total_sum"].label = _("Price")
        self.fields["attachment"].label = _("Attachment")

    def clean_exception(self):
        data = self.cleaned_data

        _exception = data.get("exception")
        _expense_type = data.get("expense_type")

        if _exception and _expense_type and _expense_type.necessary:
            msg = _(
                "The %(title)s is 'Necessary', so it can't be marked as 'Exeption'"
            ) % {"title": _expense_type.title}
            raise forms.ValidationError(msg)

        return _exception

    def clean_attachment(self):
        image = self.cleaned_data.get("attachment", False)

        with contextlib.suppress(FileNotFoundError):
            if image and image.size > 4 * 1024 * 1024:
                raise ValidationError(_("Image file too large ( > 4Mb )"))

        return image

    def clean_date(self):
        dt = self.cleaned_data["date"]

        year_user = utils.get_user().year
        year_instance = dt.year
        year_now = datetime.now().year

        diff = 1
        if (year_instance - year_now) > diff:
            year_msg = year_user + diff
            self.add_error(
                "date",
                _("Year cannot be later than %(year)s") % ({"year": year_msg}),
            )

        return dt

    def clean(self):
        cleaned_data = super().clean()

        account = cleaned_data.get("account")
        expense_date = cleaned_data.get("date")

        if not account or not account.closed:
            return cleaned_data

        if expense_date.year > account.closed:
            self.add_error(
                "date",
                _(
                    "The date cannot be later than the account closure date. The account was closed in %(year)s."
                )
                % ({"year": f"{account.closed}"}),
            )


class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = ["journal", "title", "necessary"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # journal input
        self.fields["journal"].initial = utils.get_user().journal
        self.fields["journal"].disabled = True
        self.fields["journal"].widget = forms.HiddenInput()

        self.fields["title"].label = _("Title")
        self.fields["necessary"].label = _("Necessary")

        self.helper = FormHelper()


class ExpenseNameForm(forms.ModelForm):
    class Meta:
        model = ExpenseName
        fields = ["parent", "title", "valid_for"]

        widgets = {
            "valid_for": YearPickerInput(format="%Y"),
        }

    field_order = ["parent", "title", "valid_for"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # overwrite ForeignKey parent queryset
        self.fields["parent"].queryset = ExpenseType.objects.items()

        # field labels
        self.fields["parent"].label = _("Expense type")
        self.fields["title"].label = _("Expense name")
        self.fields["valid_for"].label = _("Valid for")

        self.helper = FormHelper()

    def clean(self):
        cleaned_data = super().clean()
        form_utils.clean_year_picker_input(
            "valid_for", self.data, cleaned_data, self.errors
        )

        return cleaned_data
