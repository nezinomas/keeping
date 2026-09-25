import contextlib
from datetime import datetime
from urllib.parse import urlencode

from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import ConvertPriceMixin
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_fields import CommaFloatField
from ..core.lib.form_widgets import DatePickerWidget, YearPickerWidget
from ..core.lib.utils import int_or_zero
from .models import Expense, ExpenseName, ExpenseType
from .services.model_services import (
    ExpenseNameModelService,
    ExpenseTypeModelService,
)


class ExpenseNameChoicesMixin:
    """Needs self.user set by the form before its methods are called."""

    def names_year(self):
        return self.user.year

    def _posted_expense_type_pk(self):
        return int_or_zero(self.data.get(self.add_prefix("expense_type")))

    def _initial_expense_type_pk(self):
        initial = self.get_initial_for_field(
            self.fields["expense_type"], "expense_type"
        )

        return int_or_zero(getattr(initial, "pk", initial))

    def _instance_expense_type_pk(self):
        if self.instance.pk:
            return self.instance.expense_type.pk

        return 0

    def _expense_type_pk(self):
        pk = self._posted_expense_type_pk()
        if pk:
            return pk

        pk = self._initial_expense_type_pk()
        if pk:
            return pk

        return self._instance_expense_type_pk()

    def _overwrite_expense_name_query(self):
        self._set_expense_name_choices(self._expense_type_pk())

    def _set_expense_name_choices(self, expense_type_pk):
        qs = ExpenseNameModelService(self.user).none()

        if expense_type_pk:
            qs = (
                ExpenseNameModelService(self.user)
                .year(self.names_year())
                .filter(parent=expense_type_pk)
            )

        self.fields["expense_name"].queryset = qs

    def _set_htmx_attributes(self):
        url = reverse("expenses:load_expense_name")

        params = {}
        if self.prefix:
            params["prefix"] = self.prefix
        if self.names_year() != self.user.year:
            params["year"] = self.names_year()

        if params:
            url = f"{url}?{urlencode(params)}"

        expense_type = self.fields["expense_type"]
        expense_type.widget.attrs["hx-get"] = url
        # self["expense_name"] would cache the BoundField before labels are translated
        name = self.fields["expense_name"].get_bound_field(self, "expense_name")
        expense_type.widget.attrs["hx-target"] = f"#{name.auto_id}"
        expense_type.widget.attrs["hx-trigger"] = "change"


class ExpenseForm(ExpenseNameChoicesMixin, ConvertPriceMixin, forms.ModelForm):
    price = CommaFloatField(min_value=0.01)
    total_sum = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"inputmode": "decimal"})
    )

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
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_account_query()
        self._overwrite_expense_type_query()
        self._overwrite_expense_name_query()
        self._set_htmx_attributes()
        self._translate_fields()

        # form inputs settings
        self.fields["date"].widget = DatePickerWidget()

        self.fields["price"].widget = forms.TextInput(
            attrs={"readonly": True, "class": "disabled"}
        )
        self.fields["remark"].widget.attrs["rows"] = 3

    def _initial_fields_values(self):
        if not self.instance.pk:
            self.fields["date"].initial = set_date_with_user_year(self.user)
            self.fields["account"].initial = (
                AccountModelService(self.user).items().first()
            )
            self.fields["price"].initial = "0.00"

    def _overwrite_account_query(self):
        if self.instance.pk:
            qs = AccountModelService(self.user).items(self.instance.date.year)
        else:
            qs = AccountModelService(self.user).items()

        self.fields["account"].queryset = qs

    def _overwrite_expense_type_query(self):
        self.fields["expense_type"].queryset = ExpenseTypeModelService(
            self.user
        ).items()

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

        year_user = self.user.year
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
            self.add_error(  # noqa: RET503
                "date",
                _(
                    "The date cannot be later than the account closure date. The account was closed in %(year)s."  # noqa: E501
                )
                % ({"year": f"{account.closed}"}),
            )

        return cleaned_data


class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = ["journal", "title", "necessary"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # journal input
        self.fields["journal"].initial = user.journal
        self.fields["journal"].disabled = True
        self.fields["journal"].widget = forms.HiddenInput()

        self.fields["title"].label = _("Title")
        self.fields["necessary"].label = _("Necessary")


class ExpenseNameForm(forms.ModelForm):
    class Meta:
        model = ExpenseName
        fields = ["parent", "title", "valid_for"]

        widgets = {
            "valid_for": YearPickerWidget(),
        }

    field_order = ["parent", "title", "valid_for"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # overwrite ForeignKey parent queryset
        self.fields["parent"].queryset = ExpenseTypeModelService(user).items()

        # field labels
        self.fields["parent"].label = _("Expense type")
        self.fields["title"].label = _("Expense name")
        self.fields["valid_for"].label = _("Valid for")
