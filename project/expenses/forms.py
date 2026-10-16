import contextlib
from urllib.parse import urlencode

from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext as _

from ..accounts.forms import ACCOUNT_CLOSED
from ..accounts.services.model_services import AccountModelService
from ..core.lib import table_columns
from ..core.lib.convert_price import PriceToCentsFormMixin
from ..core.lib.form_fields import CommaFloatField, date_field, pin
from ..core.lib.form_widgets import YearPickerWidget
from ..core.lib.utils import int_or_zero
from ..core.mixins.forms import ClosedYearMixin, UserTodayMixin, YearNotLaterMixin
from .models import DEFAULT_QUANTITY, Expense, ExpenseName, ExpenseType
from .services.model_services import (
    ExpenseNameModelService,
    ExpenseTypeModelService,
)


class ExpenseNameChoicesMixin:
    """Needs self.user set by the form before its methods are called."""

    def names_year(self):
        return self.user.selected_year()

    def _posted_expense_type_pk(self):
        return int_or_zero(self.data.get(self.add_prefix("expense_type")))

    def _initial_expense_type_pk(self):
        initial = self.get_initial_for_field(
            self.fields["expense_type"], "expense_type"
        )

        return int_or_zero(getattr(initial, "pk", initial))

    def _expense_type_pk(self):
        # a ModelForm's instance reaches here through its initial
        return self._posted_expense_type_pk() or self._initial_expense_type_pk()

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
        names_year = self.names_year()
        if names_year != self.user.selected_year():
            params["year"] = names_year

        if params:
            url = f"{url}?{urlencode(params)}"

        expense_type = self.fields["expense_type"]
        expense_type.widget.attrs["hx-get"] = url
        # self["expense_name"] would cache the BoundField before labels are translated
        name = self.fields["expense_name"].get_bound_field(self, "expense_name")
        expense_type.widget.attrs["hx-target"] = f"#{name.auto_id}"
        expense_type.widget.attrs["hx-trigger"] = "change"


class ExpenseForm(
    UserTodayMixin,
    ClosedYearMixin,
    ExpenseNameChoicesMixin,
    PriceToCentsFormMixin,
    YearNotLaterMixin,
    forms.ModelForm,
):
    closed_fields = {"account": (ACCOUNT_CLOSED, "date")}
    price_fields = ("price",)
    price = CommaFloatField(min_value=0.01)
    quantity = forms.IntegerField(min_value=1, initial=DEFAULT_QUANTITY)
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
        super().__init__(*args, **kwargs)

        self._initial_fields_values()
        self._overwrite_account_query()
        self._overwrite_expense_type_query()
        self._overwrite_expense_name_query()
        self._set_htmx_attributes()
        self._translate_fields()
        self._set_widgets()

    def _set_widgets(self):
        self.fields["price"].widget = forms.TextInput(attrs={"readonly": True})
        self.fields["remark"].widget.attrs["rows"] = 3

    def _initial_fields_values(self):
        date_field(self.fields["date"], self.user, self.today)

        if self.instance.pk:
            return

        if account := AccountModelService(self.user).items().first():
            self.fields["account"].initial = account
        self.fields["price"].initial = "0.00"

    def _overwrite_account_query(self):
        service = AccountModelService(self.user)
        qs = service.items()

        if self.instance.pk:
            qs = service.items_in(self.instance.date.year)

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
        exception = self.cleaned_data["exception"]

        if not exception or "expense_type" not in self.cleaned_data:
            return exception

        expense_type = self.cleaned_data["expense_type"]
        if expense_type.necessary:
            msg = _(
                "The %(title)s is 'Necessary', so it can't be marked as 'Exeption'"
            ) % {"title": expense_type.title}
            raise ValidationError(msg)

        return exception

    def clean_attachment(self):
        image = self.cleaned_data["attachment"]

        with contextlib.suppress(FileNotFoundError):
            if image and image.size > 4 * 1024 * 1024:
                raise ValidationError(_("Image file too large ( > 4Mb )"))

        return image


class ExpenseTypeForm(UserTodayMixin, forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = ["journal", "title", "necessary"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pin(self.fields["journal"], self.user.journal)

        self.fields["title"].label = _("Title")
        self.fields["necessary"].label = _("Necessary")

    def clean_title(self):
        title = self.cleaned_data["title"]

        if title in table_columns.RESERVED:
            raise ValidationError(_("This title is reserved."))

        return title


class ExpenseNameForm(UserTodayMixin, forms.ModelForm):
    class Meta:
        model = ExpenseName
        fields = ["parent", "title", "valid_for"]

        widgets = {
            "valid_for": YearPickerWidget(),
        }

    field_order = ["parent", "title", "valid_for"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["parent"].queryset = ExpenseTypeModelService(self.user).items()

        self.fields["parent"].label = _("Expense type")
        self.fields["title"].label = _("Expense name")
        self.fields["valid_for"].label = _("Valid for")
