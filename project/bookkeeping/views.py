from datetime import date

from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.utils import http_htmx_response, wants_fragment
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.tabs import TabViewMixin as CoreTabViewMixin
from ..core.mixins.views import (
    CreateViewMixin,
    FormViewMixin,
    TemplateViewMixin,
)
from ..pensions.services.model_services import PensionTypeModelService
from ..savings.services.model_services import SavingTypeModelService
from . import balance_sources, forms, services
from .lib import no_incomes
from .mixins.month import MonthMixin
from .services.detailed.shares import with_subtitles
from .services.model_services import (
    AccountWorthModelService,
    PensionWorthModelService,
    SavingWorthModelService,
)
from .tabs import DETAILED_TABS, INDEX_TABS


class IndexTabMixin(CoreTabViewMixin):
    tabs = INDEX_TABS
    default_tab = INDEX_TABS["overview"]
    page_template = "bookkeeping/index.html"

    @property
    def app_title(self) -> str:
        return str(self.request.user.selected_year())


class TabOverview(IndexTabMixin, TemplateViewMixin):
    tab = INDEX_TABS["overview"]

    def get_context_data(self, **kwargs):
        user = self.request.user
        year = user.selected_year()
        today = date.today()
        index = services.index.load_service(user, today)
        debts = services.index.DebtsTable.load(user)
        accounts = services.accounts.load_service(user, year)

        return {
            **super().get_context_data(**kwargs),
            **accounts,
            "cash_flow_check": index.check_cash_flow(accounts["total_row"]["balance"]),
            "balance_short": index.balance_short_context(),
            **no_incomes.load_service(user, year, today),
            "wealth": services.wealth.load_service(user, year)["data"],
            "averages": index.averages_context(),
            "borrow": debts.borrow_context(),
            "lend": debts.lend_context(),
        }


class TabFunds(IndexTabMixin, TemplateViewMixin):
    tab = INDEX_TABS["funds"]

    def get_context_data(self, **kwargs):
        user = self.request.user
        year = user.selected_year()

        return {
            **super().get_context_data(**kwargs),
            "savings": services.savings.load_service(user, year),
            "pensions": services.pensions.load_service(user, year),
        }


class TabBalance(IndexTabMixin, TemplateViewMixin):
    tab = INDEX_TABS["balance"]

    def get_context_data(self, **kwargs):
        user = self.request.user
        year = user.selected_year()
        index = services.index.load_service(user, date.today())
        accounts = services.accounts.load_service(user, year)

        return {
            **super().get_context_data(**kwargs),
            "year": year,
            "balance": index.balance_context(accounts["total_row"]["balance"]),
            "expenses": services.expenses.load_service(user).table_context(),
        }


class TabCharts(IndexTabMixin, TemplateViewMixin):
    tab = INDEX_TABS["charts"]

    def get_context_data(self, **kwargs):
        user = self.request.user

        return {
            **super().get_context_data(**kwargs),
            "chart_balance": services.index.IncomesExpensesChart.load(user).context(),
            "chart_expenses": services.expenses.load_service(user).chart_context(),
        }


class RegenerateBalances(TemplateViewMixin):
    def get(self, request, *args, **kwargs):
        balances = {
            "accounts": balance_sources.sync_accounts,
            "savings": balance_sources.sync_savings,
            "pensions": balance_sources.sync_pensions,
        }
        syncs = list(balances.values())

        if (kind := request.GET.get("type")) in balances:
            syncs = [balances[kind]]

        for sync in syncs:
            sync(request.user)

        return http_htmx_response("reload")


class AccountsWorthNew(FormsetMixin, CreateViewMixin):
    service_class = AccountWorthModelService
    category_service_class = AccountModelService
    form_class = forms.AccountWorthForm
    modal_form_title = _("Worth of accounts")
    url = reverse_lazy("bookkeeping:accounts_worth_new")
    hx_trigger_django = "reload"
    balance_sync = staticmethod(balance_sources.sync_accounts)


class SavingsWorthNew(FormsetMixin, CreateViewMixin):
    service_class = SavingWorthModelService
    category_service_class = SavingTypeModelService
    form_class = forms.SavingWorthForm
    modal_form_title = _("Worth of savings")
    url = reverse_lazy("bookkeeping:savings_worth_new")
    hx_trigger_django = "reload"
    balance_sync = staticmethod(balance_sources.sync_savings)


class PensionsWorthNew(FormsetMixin, CreateViewMixin):
    service_class = PensionWorthModelService
    category_service_class = PensionTypeModelService
    form_class = forms.PensionWorthForm
    modal_form_title = _("Worth of pensions")
    url = reverse_lazy("bookkeeping:pensions_worth_new")
    hx_trigger_django = "reload"
    balance_sync = staticmethod(balance_sources.sync_pensions)


class Forecast(TemplateViewMixin):
    template_name = "bookkeeping/includes/forecast.html"

    def get_context_data(self, **kwargs):
        context = services.forecast.load_service(self.request.user, date.today())

        return super().get_context_data(**kwargs) | context


class Month(MonthMixin, TemplateViewMixin):
    template_name = "bookkeeping/month.html"

    def get_template_names(self):
        template = self.template_name

        if wants_fragment(self.request):
            template = f"{template}#page"

        return [template]

    def get_context_data(self, **kwargs):
        self.set_month()

        context = services.month.load_service(self.request.user, date.today())

        return super().get_context_data(**kwargs) | context


class MonthChart(TemplateViewMixin):
    template_name = "bookkeeping/includes/month_chart.html"


class DetailedTabMixin(CoreTabViewMixin):
    tabs = DETAILED_TABS
    default_tab = DETAILED_TABS["incomes"]
    app_title = _("Detailed")
    page_template = "bookkeeping/detailed/index.html"
    category = ""

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "months": services.detailed.MONTHS,
            "tables": services.detailed.load_service(
                self.request.user, self.category, self.request.GET.get("order", "")
            ),
        }


class TabIncomes(DetailedTabMixin, TemplateViewMixin):
    category = "income"


class TabSavings(DetailedTabMixin, TemplateViewMixin):
    tab = DETAILED_TABS["savings"]
    category = "saving"


class TabExpenses(DetailedTabMixin, TemplateViewMixin):
    tab = DETAILED_TABS["expenses"]
    category = "expenses"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context | {"tables": with_subtitles(context["tables"])}


class DetailedTable(TemplateViewMixin):
    template_name = "cotton/detailed_table.html"

    def get_context_data(self, **kwargs):
        tables = services.detailed.load_service(
            user=self.request.user,
            category=self.kwargs["category"],
            order=self.request.GET.get("order", ""),
            type_slug=self.kwargs.get("type_slug", ""),
        )
        context = super().get_context_data(**kwargs)
        context["months"] = services.detailed.MONTHS

        if tables:
            context |= tables[0]

        return context


class Summary(TemplateViewMixin):
    template_name = "bookkeeping/summary.html"

    def get_context_data(self, **kwargs):
        context = services.chart_summary.load_service(self.request.user, date.today())
        return super().get_context_data(**kwargs) | context


class SummarySavings(TemplateViewMixin):
    template_name = "bookkeeping/summary_savings.html"

    def get_context_data(self, **kwargs):
        context = services.summary_savings.load(self.request.user, date.today())
        return super().get_context_data(**kwargs) | context


class SummarySavingsAndIncomes(TemplateViewMixin):
    template_name = "bookkeeping/summary_savings_and_incomes.html"

    def get_context_data(self, **kwargs):
        context = services.summary_savings_and_incomes.load_service(
            self.request.user, date.today()
        )
        return super().get_context_data(**kwargs) | context


class SummaryExpenses(FormViewMixin):
    form_class = forms.SummaryExpensesForm
    template_name = "bookkeeping/summary_expenses.html"
    success_url = reverse_lazy("bookkeeping:summary_expenses")

    def form_valid(self, form):
        form_data = form.cleaned_data["types"]
        context = {
            "form": form,
            **services.chart_summary_expenses.load_service(
                self.request.user, form_data
            ),
        }

        return render(self.request, self.template_name, context)


class ExpandDayExpenses(TemplateViewMixin):
    template_name = "bookkeeping/includes/expand_day_expenses.html"

    def get_context_data(self, **kwargs):
        obj = services.expand_day.ExpandDayService(
            self.request.user, self.kwargs["date"]
        )

        return super().get_context_data(**kwargs) | obj.context()
