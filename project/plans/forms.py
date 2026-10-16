from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import transaction
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from ..core.lib.convert_price import PriceToCentsFormMixin, int_cents_to_float
from ..core.lib.date import monthnames
from ..core.lib.form_fields import CommaFloatField
from ..core.lib.form_widgets import YearPickerWidget
from ..core.lib.translation import month_names
from ..core.mixins.forms import UserTodayMixin
from ..expenses.services.model_services import ExpenseTypeModelService
from ..incomes.services.model_services import IncomeTypeModelService
from ..savings.services.model_services import SavingTypeModelService
from .models import (
    DayPlan,
    ExpensePlan,
    IncomePlan,
    NecessaryPlan,
    SavingPlan,
)
from .services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    NecessaryPlanModelService,
    SavingPlanModelService,
)

MONTH_FIELD_KWARGS = {"min_value": 0.01, "required": False}

COPY_PLANS = {
    "income": {
        "service": IncomePlanModelService,
        "label": gettext_lazy("Incomes plans"),
    },
    "expense": {
        "service": ExpensePlanModelService,
        "label": gettext_lazy("Expenses plans"),
    },
    "saving": {
        "service": SavingPlanModelService,
        "label": gettext_lazy("Savings plans"),
    },
    "day": {"service": DayPlanModelService, "label": gettext_lazy("Day plans")},
    "necessary": {
        "service": NecessaryPlanModelService,
        "label": gettext_lazy("Plans for additional necessary expenses"),
    },
}


class CommonPlanFormMixin(UserTodayMixin, PriceToCentsFormMixin, forms.ModelForm):
    price_fields = tuple(monthnames())

    january = CommaFloatField(**MONTH_FIELD_KWARGS)
    february = CommaFloatField(**MONTH_FIELD_KWARGS)
    march = CommaFloatField(**MONTH_FIELD_KWARGS)
    april = CommaFloatField(**MONTH_FIELD_KWARGS)
    may = CommaFloatField(**MONTH_FIELD_KWARGS)
    june = CommaFloatField(**MONTH_FIELD_KWARGS)
    july = CommaFloatField(**MONTH_FIELD_KWARGS)
    august = CommaFloatField(**MONTH_FIELD_KWARGS)
    september = CommaFloatField(**MONTH_FIELD_KWARGS)
    october = CommaFloatField(**MONTH_FIELD_KWARGS)
    november = CommaFloatField(**MONTH_FIELD_KWARGS)
    december = CommaFloatField(**MONTH_FIELD_KWARGS)

    class Meta:
        widgets = {
            "year": YearPickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._setup_year_field()
        self._translate_common_fields()

        self._load_month_prices()
        self._set_grouping_fields_readonly()

    def clean(self):
        cleaned_data = super().clean()

        if self.errors or self.instance.pk:
            return cleaned_data

        year = cleaned_data.get("year")
        grouping_data = self._extract_grouping_data(cleaned_data)

        if self._does_plan_exist(year, grouping_data):
            self._raise_duplicate_plan_error(year, grouping_data)

        return cleaned_data

    def save(self):
        grouping = self._grouping_data()
        existing = self._existing_rows(grouping)
        created, changed, emptied = [], [], []

        for month, month_name in enumerate(monthnames(), start=1):
            price = self.cleaned_data.get(month_name)

            if not price:
                if month in existing:
                    emptied.append(existing[month].pk)
                continue

            if month not in existing:
                created.append(self._new_row(month, price, grouping))
                continue

            row = existing[month]
            if row.price != price:
                row.price = price
                changed.append(row)

        model = self.Meta.model
        with transaction.atomic():
            model.objects.bulk_create(created)
            model.objects.bulk_update(changed, ["price"])
            model.objects.filter(pk__in=emptied).delete()

        return self.instance

    def _grouping_data(self):
        return {f: self.cleaned_data[f] for f in self.Meta.grouping_fields}

    def _existing_rows(self, grouping):
        service = self.Meta.service_class(self.user)
        rows = service.objects.filter(year=self.cleaned_data["year"], **grouping)
        return {row.month: row for row in rows}

    def _new_row(self, month, price, grouping):
        return self.Meta.model(
            year=self.cleaned_data["year"],
            month=month,
            journal=self.user.journal,
            price=price,
            **grouping,
        )

    def _translate_common_fields(self):
        self.fields["year"].label = _("Years")

        for key, val in month_names().items():
            self.fields[key.lower()].label = val

    def _setup_year_field(self):
        self.fields["year"].initial = self.user.selected_year()

    def _load_month_prices(self):
        if not self.instance.pk:
            return

        filter_kwargs = {"year": self.instance.year, "journal": self.user.journal}
        for field_name in self.Meta.grouping_fields:
            filter_kwargs[field_name] = getattr(self.instance, field_name)

        service = self.Meta.service_class(self.user)
        rows = service.objects.filter(**filter_kwargs)

        months = monthnames()
        for row in rows:
            # a stored 0 would fail the month field's min_value=0.01 on re-save
            if not row.price:
                continue

            self.initial[months[row.month - 1]] = int_cents_to_float(row.price)

    def _set_field_readonly(self, field_name):
        self.fields[field_name].disabled = True
        self.fields[field_name].widget.attrs["readonly"] = True

    def _set_grouping_fields_readonly(self):
        if not self.instance.pk:
            return

        self._set_field_readonly("year")

        for field_name in self.Meta.grouping_fields:
            self._set_field_readonly(field_name)

    def _extract_grouping_data(self, cleaned_data):
        return {
            f: cleaned_data.get(f)
            for f in self.Meta.grouping_fields
            if f in cleaned_data
        }

    def _does_plan_exist(self, year, grouping_data):
        lookup = {"year": year, "journal": self.user.journal, **grouping_data}
        service = self.Meta.service_class(self.user)
        return service.objects.filter(**lookup).exists()

    def _duplicate_message(self, year, grouping_data):
        if not self.Meta.grouping_fields:
            return _("Plan for %(year)s already exists.") % {"year": year}

        values = _(" and ").join(str(v) for v in grouping_data.values())
        return _("A plan for %(year)s with %(values)s already exists.") % {
            "year": year,
            "values": f"'{values}'",
        }

    def _raise_duplicate_plan_error(self, year, grouping_data):
        error_msg = self._duplicate_message(year, grouping_data)
        errors_dict = {"__all__": error_msg, "year": ""}
        for field in self.Meta.grouping_fields:
            errors_dict[field] = ""

        raise forms.ValidationError(errors_dict)


class IncomePlanForm(CommonPlanFormMixin):
    class Meta(CommonPlanFormMixin.Meta):
        model = IncomePlan
        service_class = IncomePlanModelService

        grouping_fields = ["income_type"]
        fields = ["year", *grouping_fields, *monthnames()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["income_type"].queryset = IncomeTypeModelService(self.user).items()
        self.fields["income_type"].label = _("Income type")


class ExpensePlanForm(CommonPlanFormMixin):
    class Meta(CommonPlanFormMixin.Meta):
        model = ExpensePlan
        service_class = ExpensePlanModelService

        grouping_fields = ["expense_type"]
        fields = ["year", *grouping_fields, *monthnames()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["expense_type"].queryset = ExpenseTypeModelService(
            self.user
        ).items()
        self.fields["expense_type"].label = _("Expense type")


class SavingPlanForm(CommonPlanFormMixin):
    class Meta(CommonPlanFormMixin.Meta):
        model = SavingPlan
        service_class = SavingPlanModelService

        grouping_fields = ["saving_type"]
        fields = ["year", *grouping_fields, *monthnames()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["saving_type"].queryset = SavingTypeModelService(self.user).items()
        self.fields["saving_type"].label = _("Saving type")


class DayPlanForm(CommonPlanFormMixin):
    class Meta(CommonPlanFormMixin.Meta):
        model = DayPlan
        service_class = DayPlanModelService

        grouping_fields = []
        fields = ["year", *grouping_fields, *monthnames()]


class NecessaryPlanForm(CommonPlanFormMixin):
    class Meta(CommonPlanFormMixin.Meta):
        model = NecessaryPlan
        service_class = NecessaryPlanModelService

        grouping_fields = ["expense_type", "title"]
        fields = ["year", *grouping_fields, *monthnames()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["expense_type"].queryset = ExpenseTypeModelService(
            self.user
        ).items()
        self.fields["expense_type"].label = _("Expense type")


class CopyPlanForm(UserTodayMixin, forms.Form):
    year_from = forms.IntegerField(
        widget=YearPickerWidget(),
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    year_to = forms.IntegerField(
        widget=YearPickerWidget(),
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._setup_initial_values()
        self._translate_fields()
        self._add_copy_checkboxes()

    def clean(self):
        cleaned_data = super().clean()
        year_from = cleaned_data.get("year_from")
        year_to = cleaned_data.get("year_to")

        if self.errors or not year_from or not year_to:
            return cleaned_data

        checkboxes = self._extract_selected_checkboxes(cleaned_data)
        if not any(checkboxes.values()):
            raise forms.ValidationError(_("At least one plan needs to be selected."))

        self._validate_copy_operation(checkboxes, year_from, year_to)

        return cleaned_data

    @transaction.atomic
    def save(self):
        dict_ = self._extract_selected_checkboxes(self.cleaned_data)
        year_from = self.cleaned_data["year_from"]
        year_to = self.cleaned_data["year_to"]

        for k, v in dict_.items():
            if not v:
                continue

            service = COPY_PLANS[k]["service"](self.user)
            source_rows = list(service.year(year_from))

            for obj in source_rows:
                obj.pk = None
                obj.year = year_to

            service.objects.bulk_create(source_rows)

    def _setup_initial_values(self):
        self.fields["year_from"].initial = self.today.year
        self.fields["year_to"].initial = self.today.year + 1

    def _translate_fields(self):
        self.fields["year_from"].label = _("Copy from")
        self.fields["year_to"].label = _("Copy to")

    def _add_copy_checkboxes(self):
        for kind, plan in COPY_PLANS.items():
            self.fields[kind] = forms.BooleanField(
                required=False, label=plan["label"], initial=True
            )

    def _extract_selected_checkboxes(self, cleaned_data):
        return {kind: cleaned_data.get(kind) for kind in COPY_PLANS}

    def _validate_copy_operation(self, checkboxes, year_from, year_to):
        errors = {}
        msg_empty = _("There is nothing to copy.")
        msg_exists = _("%(year)s year already has plans.") % {"year": year_to}

        for k, v in checkboxes.items():
            if not v:
                continue

            service = COPY_PLANS[k]["service"](self.user)

            if not service.year(year_from).exists():
                errors.setdefault(k, []).append(msg_empty)

            if service.year(year_to).exists():
                errors.setdefault(k, []).append(msg_exists)

        if errors:
            raise forms.ValidationError(errors)
