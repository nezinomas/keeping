from datetime import date

from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..accounts.models import Account
from ..core.lib.date import monthnames_abbr
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import (
    CreateViewMixin,
    FormViewMixin,
    TemplateViewMixin,
    rendered_content,
)
from ..pensions.models import PensionType
from ..savings.models import SavingType
from . import forms, models, services
from .lib import no_incomes
from .mixins.month import MonthMixin


class ReloadIndexContextDataMixin:
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        ind = services.index.load_service(year)
        exp = services.expenses.load_service(year)

        context = {
            "year": self.request.user.year,
            "averages": ind.averages_context(),
            "borrow": ind.borrow_context(),
            "lend": ind.lend_context(),
            "balance_short": ind.balance_short_context(),
            "balance": ind.balance_context(),
            "chart_balance": ind.chart_balance_context(),
            "chart_expenses": exp.chart_context(),
            "expenses": exp.table_context(),
        }
        return super().get_context_data(**kwargs) | context


class Index(ReloadIndexContextDataMixin, TemplateViewMixin):
    template_name = "bookkeeping/index.html"

    def get_context_data(self, **kwargs):
        context = {
            "accounts": rendered_content(self.request, Accounts, **self.kwargs),
            "savings": rendered_content(self.request, Savings, **self.kwargs),
            "pensions": rendered_content(self.request, Pensions, **self.kwargs),
            "wealth": rendered_content(self.request, Wealth, **self.kwargs),
            "no_incomes": rendered_content(self.request, NoIncomes, **self.kwargs),
        }
        return super().get_context_data(**kwargs) | context


class ReloadIndex(ReloadIndexContextDataMixin, TemplateViewMixin):
    template_name = "bookkeeping/includes/reload_index.html"


class Accounts(TemplateViewMixin):
    template_name = "bookkeeping/includes/account_worth_list.html"

    def get_context_data(self, **kwargs):
        context = services.accounts.load_service(self.request.user.year)

        return super().get_context_data(**kwargs) | context


class AccountsWorthNew(FormsetMixin, CreateViewMixin):
    type_model = Account
    model = models.AccountWorth
    form_class = forms.AccountWorthForm
    formset_title = _("Worth of accounts")
    url = reverse_lazy("bookkeeping:accounts_worth_new")
    hx_trigger_django = "afterAccountWorthNew"


class Savings(TemplateViewMixin):
    template_name = "bookkeeping/savings.html"

    def get_context_data(self, **kwargs):
        context = services.savings.load_service(self.request.user.year)
        return super().get_context_data(**kwargs) | context


class SavingsWorthNew(FormsetMixin, CreateViewMixin):
    type_model = SavingType
    model = models.SavingWorth
    form_class = forms.SavingWorthForm
    formset_title = _("Worth of savings")
    url = reverse_lazy("bookkeeping:savings_worth_new")
    hx_trigger_django = "afterSavingWorthNew"


class Pensions(TemplateViewMixin):
    template_name = "bookkeeping/includes/funds_table.html"

    def get_context_data(self, **kwargs):
        context = services.pensions.load_service(self.request.user.year)

        return super().get_context_data(**kwargs) | context


class PensionsWorthNew(FormsetMixin, CreateViewMixin):
    type_model = PensionType
    model = models.PensionWorth
    form_class = forms.PensionWorthForm
    formset_title = _("Worth of pensions")
    url = reverse_lazy("bookkeeping:pensions_worth_new")
    hx_trigger_django = "afterPensionWorthNew"


class Wealth(TemplateViewMixin):
    template_name = "cotton/info_table.html"

    def get_context_data(self, **kwargs):
        context = services.wealth.load_service(self.request.user.year)
        return super().get_context_data(**kwargs) | context


class Forecast(TemplateViewMixin):
    template_name = "bookkeeping/includes/forecast.html"

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        context = services.forecast.load_service(year)

        return super().get_context_data(**kwargs) | context


class NoIncomes(TemplateViewMixin):
    template_name = "bookkeeping/includes/no_incomes.html"

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        journal = self.request.user.journal
        context = no_incomes.load_service(year, journal)

        return super().get_context_data(**kwargs) | context


class Month(MonthMixin, TemplateViewMixin):
    template_name = "bookkeeping/month.html"

    def get_context_data(self, **kwargs):
        self.set_month()

        user = self.request.user
        context = services.month.load_service(user.year, user.month)

        return super().get_context_data(**kwargs) | context


class MonthChart(TemplateViewMixin):
    template_name = "bookkeeping/includes/month_chart.html"


class Detailed(TemplateViewMixin):
    template_name = "bookkeeping/detailed.html"

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        context = services.detailed.load_service(year)
        context["months"] = monthnames_abbr()

        return super().get_context_data(**kwargs) | context


class DetailedCategory(TemplateViewMixin):
    template_name = "cotton/detailed_table.html"

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        context = services.detailed_one_category.load_service(
            year, self.kwargs["order"], self.kwargs["category"]
        )
        context["order"] = self.kwargs["order"]
        context["months"] = monthnames_abbr()

        return super().get_context_data(**kwargs) | context


class Summary(TemplateViewMixin):
    template_name = "bookkeeping/summary.html"

    def get_context_data(self, **kwargs):
        context = services.chart_summary.load_service()
        return super().get_context_data(**kwargs) | context


class SummarySavings(TemplateViewMixin):
    template_name = "bookkeeping/summary_savings.html"

    def get_context_data(self, **kwargs):
        data = services.summary_savings.get_data()
        context = services.summary_savings.load_service(data)
        return super().get_context_data(**kwargs) | context


class SummarySavingsAndIncomes(TemplateViewMixin):
    template_name = "bookkeeping/summary_savings_and_incomes.html"

    def get_context_data(self, **kwargs):
        context = services.summary_savings_and_incomes.load_service()
        return super().get_context_data(**kwargs) | context


class SummaryExpenses(FormViewMixin):
    form_class = forms.SummaryExpensesForm
    template_name = "bookkeeping/summary_expenses.html"
    success_url = reverse_lazy("bookkeeping:summary_expenses")

    def form_valid(self, form, **kwargs):
        form_data = form.cleaned_data.get("types")
        context = {
            "form": form,
            **services.chart_summary_expenses.load_service(form_data),
        }

        return render(self.request, self.template_name, context)


class ExpandDayExpenses(TemplateViewMixin):
    template_name = "bookkeeping/includes/expand_day_expenses.html"

    def get_context_data(self, **kwargs):
        obj = services.expand_day.ExpandDayService(
            self.kwargs.get("date") or date(1974, 1, 1)
        )

        return super().get_context_data(**kwargs) | obj.context()
