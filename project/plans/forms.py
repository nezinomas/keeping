from datetime import datetime

from django import forms
from django.apps import apps
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext as _

from ..core.lib.convert_price import PlansConvertPriceMixin
from ..core.lib.date import monthnames, set_date_with_user_year
from ..core.lib.form_widgets import YearPickerWidget
from ..core.lib.translation import month_names
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
from .services.model_services import ModelService


def common_field_transalion(self):
    self.fields["year"].label = _("Years")

    for key, val in month_names().items():
        self.fields[key.lower()].label = val


def set_journal_field(user, fields):
    # journal input
    fields["journal"].initial = user.journal
    fields["journal"].disabled = True
    fields["journal"].widget = forms.HiddenInput()


class YearFormMixin(PlansConvertPriceMixin, forms.ModelForm):
    january = forms.FloatField(min_value=0.01, required=False)
    february = forms.FloatField(min_value=0.01, required=False)
    march = forms.FloatField(min_value=0.01, required=False)
    april = forms.FloatField(min_value=0.01, required=False)
    may = forms.FloatField(min_value=0.01, required=False)
    june = forms.FloatField(min_value=0.01, required=False)
    july = forms.FloatField(min_value=0.01, required=False)
    august = forms.FloatField(min_value=0.01, required=False)
    september = forms.FloatField(min_value=0.01, required=False)
    october = forms.FloatField(min_value=0.01, required=False)
    november = forms.FloatField(min_value=0.01, required=False)
    december = forms.FloatField(min_value=0.01, required=False)


# ----------------------------------------------------------------------------
#                                                             Income Plan Form
# ----------------------------------------------------------------------------
class IncomePlanForm(YearFormMixin):
    class Meta:
        model = IncomePlan
        fields = ["journal", "year", "income_type"] + monthnames()

        widgets = {
            "year": YearPickerWidget(),
        }

    field_order = ["year", "income_type"] + monthnames()

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(user, self.fields)

        # inital values
        self.fields["year"].initial = set_date_with_user_year(user).year

        # overwrite ForeignKey expense_type queryset
        self.fields["income_type"].queryset = IncomeTypeModelService(user).items()

        # field translation
        self.fields["income_type"].label = _("Income type")
        common_field_transalion(self)


# ----------------------------------------------------------------------------
#                                                            Expense Plan Form
# ----------------------------------------------------------------------------
class ExpensePlanForm(YearFormMixin):
    class Meta:
        model = ExpensePlan
        fields = ["journal", "year", "expense_type"] + monthnames()

        widgets = {
            "year": YearPickerWidget(),
        }

    field_order = ["year", "expense_type"] + monthnames()

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(user, self.fields)

        # inital values
        self.fields["year"].initial = set_date_with_user_year(user).year

        # overwrite ForeignKey expense_type queryset
        self.fields["expense_type"].queryset = ExpenseTypeModelService(user).items()

        # field translation
        self.fields["expense_type"].label = _("Expense type")
        common_field_transalion(self)


# ----------------------------------------------------------------------------
#                                                              Saving Plan Form
# ----------------------------------------------------------------------------
class SavingPlanForm(YearFormMixin):
    class Meta:
        model = SavingPlan
        fields = ["journal", "year", "saving_type"] + monthnames()

        widgets = {
            "year": YearPickerWidget(),
        }

    field_order = ["year", "saving_type"] + monthnames()

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(user, self.fields)

        # overwrite ForeignKey expense_type queryset
        self.fields["saving_type"].queryset = SavingTypeModelService(user).items()

        # inital values
        self.fields["year"].initial = set_date_with_user_year(user).year

        # field translation
        self.fields["saving_type"].label = _("Saving type")
        common_field_transalion(self)


# ----------------------------------------------------------------------------
#                                                                Day Plan Form
# ----------------------------------------------------------------------------
class DayPlanForm(YearFormMixin):
    class Meta:
        model = DayPlan
        fields = ["journal", "year"] + monthnames()

        widgets = {
            "year": YearPickerWidget(),
        }

    field_order = ["year"] + monthnames()

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(user, self.fields)

        # inital values
        self.fields["year"].initial = set_date_with_user_year(user).year

        # field translation
        common_field_transalion(self)


# ----------------------------------------------------------------------------
#                                                          Necessary Plan Form
# ----------------------------------------------------------------------------
class NecessaryPlanForm(YearFormMixin):
    class Meta:
        model = NecessaryPlan
        fields = ["journal", "year", "expense_type", "title"] + monthnames()

        widgets = {
            "year": YearPickerWidget(),
        }

    field_order = ["year", "expense_type", "title"] + monthnames()

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # journal input
        set_journal_field(user, self.fields)

        # inital values
        self.fields["year"].initial = set_date_with_user_year(user).year

        # overwrite ForeignKey expense_type queryset
        self.fields["expense_type"].queryset = ExpenseTypeModelService(user).items()

        # field translation
        self.fields["expense_type"].label = _("Expense type")
        common_field_transalion(self)


# ----------------------------------------------------------------------------
#                                                               Copy Plan Form
# ----------------------------------------------------------------------------
class CopyPlanForm(forms.Form):
    year_from = forms.IntegerField(
        widget=YearPickerWidget(),
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    year_to = forms.IntegerField(
        widget=YearPickerWidget(),
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    income = forms.BooleanField(required=False)
    expense = forms.BooleanField(required=False)
    saving = forms.BooleanField(required=False)
    day = forms.BooleanField(required=False)
    necessary = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def _get_cleaned_checkboxes(self, cleaned_data):
        return {
            "income": cleaned_data.get("income"),
            "expense": cleaned_data.get("expense"),
            "saving": cleaned_data.get("saving"),
            "day": cleaned_data.get("day"),
            "necessary": cleaned_data.get("necessary"),
        }

    def _get_model(self, name):
        return apps.get_model(f"plans.{name.title()}Plan")

    def _append_error_message(self, msg, errors, key):
        if err := errors.get(key):
            err.append(msg)
            errors[key] = err
        else:
            errors[key] = [msg]

    def clean(self):
        cleaned_data = super().clean()
        dict_ = self._get_cleaned_checkboxes(cleaned_data)

        year_from = cleaned_data.get("year_from")
        year_to = cleaned_data.get("year_to")

        if not year_to or not year_from:
            return cleaned_data

        # at least one checkbox must be selected
        chk = [v for k, v in dict_.items() if v]

        if not chk:
            raise forms.ValidationError(_("At least one plan needs to be selected."))

        # copy from table must contain data
        errors = {}
        msg = _("There is nothing to copy.")
        for k, v in dict_.items():
            if v:
                model = self._get_model(k)
                qs = ModelService(model, self.user).year(year_from)
                if not qs.exists():
                    self._append_error_message(msg, errors, k)

        # copy to table must be empty
        msg = _("%(year)s year already has plans.") % ({"year": year_to})

        for k, v in dict_.items():
            if v:
                model = self._get_model(k)
                qs = ModelService(model, self.user).year(year_to)
                if qs.exists():
                    self._append_error_message(msg, errors, k)

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data

    def save(self):
        dict_ = self._get_cleaned_checkboxes(self.cleaned_data)
        year_from = self.cleaned_data.get("year_from")
        year_to = self.cleaned_data.get("year_to")

        for k, v in dict_.items():
            if v:
                model = self._get_model(k)
                qs = (
                    ModelService(model, self.user)
                    .year(year_from)
                    .values_list("pk", flat=True)
                )

                for i in qs:
                    obj = model.objects.get(pk=i)
                    obj.pk = None
                    obj.year = year_to
                    obj.save()

        # initail values
        self.fields["year_from"].initial = datetime.now().year
        self.fields["year_to"].initial = datetime.now().year + 1
        self.fields["income"].initial = True
        self.fields["expense"].initial = True
        self.fields["saving"].initial = True
        self.fields["day"].initial = True
        self.fields["necessary"].initial = True

        # labels
        self.fields["year_from"].label = _("Copy from")
        self.fields["year_to"].label = _("Copy to")
        self.fields["income"].label = _("Incomes plans")
        self.fields["expense"].label = _("Expenses plans")
        self.fields["saving"].label = _("Savings plans")
        self.fields["day"].label = _("Day plans")
        self.fields["necessary"].label = _("Plans for additional necessary expenses")
