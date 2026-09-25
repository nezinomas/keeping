from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import ConvertPriceMixin, int_cents_to_float
from ..core.lib.date import set_date_with_user_year
from ..core.lib.form_fields import CommaFloatField, PreloadedModelChoiceField
from ..core.lib.form_widgets import DatePickerWidget
from .forms import ExpenseNameChoicesMixin
from .keywords import normalise_keyword
from .models import ExpenseKeyword, ExpenseName, ExpenseType
from .receipts.receipt import ReceiptLine
from .services.keyword_match import KeywordMatcher
from .services.model_services import ExpenseTypeModelService
from .services.receipt_import import ReviewedLine
from .services.review_choices import ReviewChoices


class _JournalAccountChoicesMixin:
    def _limit_account_to_journal(self):
        accounts = AccountModelService(self.user).items()
        self.fields["account"].queryset = accounts
        return accounts


class ReceiptUploadForm(_JournalAccountChoicesMixin, forms.Form):
    pdf = forms.FileField()
    date = forms.DateField(widget=DatePickerWidget())
    account = forms.ModelChoiceField(queryset=Account.objects.none())

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        accounts = self._limit_account_to_journal()
        self.fields["date"].initial = set_date_with_user_year(user)
        self.fields["account"].initial = accounts.first()
        self._translate_fields()

    def _translate_fields(self):
        self.fields["pdf"].label = _("PDF file")
        self.fields["date"].label = _("Date")
        self.fields["account"].label = _("Account")

    def clean_pdf(self):
        pdf = self.cleaned_data["pdf"]
        if not pdf.name.lower().endswith(".pdf"):
            raise ValidationError(_("Only PDF files can be imported."))

        return pdf


class ReviewReceiptForm(_JournalAccountChoicesMixin, forms.Form):
    date = forms.DateField()
    account = forms.ModelChoiceField(queryset=Account.objects.none())
    total = forms.IntegerField(widget=forms.HiddenInput())
    shop_money = forms.IntegerField(min_value=0, widget=forms.HiddenInput())
    shop_money_line = forms.IntegerField(
        min_value=0, required=False, widget=forms.HiddenInput()
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self._limit_account_to_journal()

    def clean_shop_money_line(self):
        return self.cleaned_data.get("shop_money_line") or 0

    @classmethod
    def initial_from(cls, receipt, date, account) -> dict:
        shop_money_line = 0
        if receipt.shop_money > 0:
            prices = [line.price for line in receipt.lines]
            shop_money_line = prices.index(max(prices))

        return {
            "date": date,
            "account": account,
            "total": receipt.total,
            "shop_money": receipt.shop_money,
            "shop_money_line": shop_money_line,
        }


class ReviewLineForm(ExpenseNameChoicesMixin, ConvertPriceMixin, forms.Form):
    title = forms.CharField(required=False)
    amount = forms.IntegerField(required=False)
    price = CommaFloatField(required=False)
    is_deposit = forms.BooleanField(required=False, widget=forms.HiddenInput())
    skip = forms.BooleanField(required=False)
    expense_type = PreloadedModelChoiceField(
        queryset=ExpenseType.objects.none(), required=False
    )
    expense_name = PreloadedModelChoiceField(
        queryset=ExpenseName.objects.none(), required=False
    )
    keyword = forms.CharField(
        required=False,
        max_length=ExpenseKeyword._meta.get_field("keyword").max_length,
    )

    _required_fields = (
        "title",
        "amount",
        "price",
        "expense_type",
        "expense_name",
        "keyword",
    )

    def __init__(self, *args, user, year, **kwargs):
        self.user = user
        self.year = year
        if "choices" not in kwargs:
            kwargs["choices"] = ReviewChoices.load(user, year)
        self.choices = kwargs.pop("choices")
        super().__init__(*args, **kwargs)

        self.fields["expense_type"].queryset = ExpenseTypeModelService(user).items()
        self.fields["expense_type"].preload(self.choices.types)
        self._overwrite_expense_name_query()
        self._set_htmx_attributes()
        self._translate_fields()

    def names_year(self):
        return self.year

    def _instance_expense_type_pk(self):
        return 0

    def _set_expense_name_choices(self, expense_type_pk):
        super()._set_expense_name_choices(expense_type_pk)
        self.fields["expense_name"].preload(self.choices.names_for(expense_type_pk))

    def _translate_fields(self):
        self.fields["title"].label = _("Product")
        self.fields["amount"].label = _("Quantity")
        self.fields["price"].label = _("Price")
        self.fields["skip"].label = _("Skip")
        self.fields["expense_type"].label = _("Type")
        self.fields["expense_name"].label = _("Title")
        self.fields["keyword"].label = _("Keyword")

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("skip"):
            return self._clean_skipped_row(cleaned_data)

        return self._clean_active_row(cleaned_data)

    def _clean_skipped_row(self, cleaned_data):
        # skipped → valid whatever its other fields hold, even an unparsable one;
        # reviewed_lines() never reads a skipped row's values
        for name in self._required_fields:
            self.errors.pop(name, None)

        return cleaned_data

    def _clean_active_row(self, cleaned_data):
        self._require_fields(cleaned_data)
        self._validate_price(cleaned_data)
        self._validate_amount(cleaned_data)
        self._validate_keyword(cleaned_data)

        return cleaned_data

    def _require_fields(self, cleaned_data):
        for name in self._required_fields:
            if name in self.errors:
                continue
            if cleaned_data.get(name) not in (None, ""):
                continue
            self.add_error(
                name,
                ValidationError(
                    self.fields[name].error_messages["required"], code="required"
                ),
            )

    def _validate_positive(self, cleaned_data, field_name: str, error_msg: str):
        val = cleaned_data.get(field_name)
        if val is None or field_name in self.errors:
            return
        if val <= 0:
            self.add_error(field_name, error_msg)

    def _validate_price(self, cleaned_data):
        self._validate_positive(
            cleaned_data, "price", _("Price must be greater than zero.")
        )

    def _validate_amount(self, cleaned_data):
        self._validate_positive(
            cleaned_data, "amount", _("Quantity must be greater than zero.")
        )

    def _validate_keyword(self, cleaned_data):
        keyword = cleaned_data.get("keyword")
        if not keyword or "keyword" in self.errors:
            return

        normalised = normalise_keyword(keyword)
        if len(normalised) < 3:
            self.add_error("keyword", _("Keyword must be at least 3 characters."))
            return

        title = cleaned_data.get("title") or ""
        if normalised not in title.casefold():
            self.add_error("keyword", _("Keyword must appear in the product title."))
            return

        cleaned_data["keyword"] = normalised


class _ReviewFormSet(forms.BaseFormSet):
    def __init__(self, *args, shop_money=0, shop_money_line=0, **kwargs):
        self.shop_money = shop_money
        self.shop_money_line = shop_money_line

        form_kwargs = kwargs["form_kwargs"]
        choices = ReviewChoices.load(form_kwargs["user"], form_kwargs["year"])
        kwargs["form_kwargs"] = form_kwargs | {"choices": choices}

        super().__init__(*args, **kwargs)

    def clean(self):
        if any(self.errors):
            return

        self._check_duplicate_keywords()
        self._check_shop_money()

    def _check_duplicate_keywords(self):
        by_keyword: dict[str, list[tuple[forms.Form, ExpenseName]]] = {}
        for form in self.forms:
            if form.cleaned_data.get("skip"):
                continue

            keyword = form.cleaned_data.get("keyword")
            if not keyword:
                continue

            by_keyword.setdefault(keyword, []).append(
                (form, form.cleaned_data.get("expense_name"))
            )

        for rows in by_keyword.values():
            names = {name for _form, name in rows}
            if len(names) <= 1:
                continue

            for form, _name in rows:
                form.add_error(
                    "keyword",
                    _("The same keyword is used for different expense names."),
                )

    def _check_shop_money(self):
        if self.shop_money <= 0:
            return

        index = self.shop_money_line
        if not (0 <= index < len(self.forms)):
            raise ValidationError(_("The Shop money line is not on this receipt."))

        row = self.forms[index]
        if row.cleaned_data.get("skip"):
            row.add_error(None, _("Shop money cannot go on a skipped line."))
            return

        price = row.cleaned_data.get("price") or 0
        if price - self.shop_money <= 0:
            row.add_error(
                "price", _("Shop money would leave this price at zero or below.")
            )

    def reviewed_lines(self) -> tuple[ReviewedLine, ...]:
        lines = []
        for index, form in enumerate(self.forms):
            data = form.cleaned_data
            if data.get("skip"):
                continue

            line = ReceiptLine(
                title=data["title"],
                amount=data["amount"],
                price=data["price"],
                is_deposit=data["is_deposit"],
            )
            lines.append(
                ReviewedLine(
                    line=line,
                    expense_name=data["expense_name"],
                    keyword=data["keyword"],
                    carries_shop_money=(
                        self.shop_money > 0 and index == self.shop_money_line
                    ),
                )
            )

        return tuple(lines)

    @classmethod
    def initial_from(cls, receipt, keywords) -> list[dict]:
        rows = []
        for line in receipt.lines:
            row = {
                "title": line.title,
                "amount": line.amount,
                "price": int_cents_to_float(line.price),
                "is_deposit": line.is_deposit,
            }
            row |= KeywordMatcher.match(line.title, keywords).initial()
            rows.append(row)

        return rows


ReviewFormSet = forms.formset_factory(ReviewLineForm, formset=_ReviewFormSet, extra=0)
