from django.urls import path, register_converter

from ..core import converters
from . import views
from .apps import App_name

app_name = App_name

register_converter(converters.DateConverter, "date")

urlpatterns = [
    path("", views.TabOverview.as_view(), name="index"),
    path("", views.TabOverview.as_view(), name="tab_overview"),
    path("bookkeeping/funds/", views.TabFunds.as_view(), name="tab_funds"),
    path("bookkeeping/balance/", views.TabBalance.as_view(), name="tab_balance"),
    path("bookkeeping/charts/", views.TabCharts.as_view(), name="tab_charts"),
    path(
        "set/balances/", views.RegenerateBalances.as_view(), name="regenerate_balances"
    ),
    path(
        "bookkeeping/accounts_worth/new/",
        views.AccountsWorthNew.as_view(),
        name="accounts_worth_new",
    ),
    path(
        "bookkeeping/savings_worth/new/",
        views.SavingsWorthNew.as_view(),
        name="savings_worth_new",
    ),
    path(
        "bookkeeping/pensions_worth/new/",
        views.PensionsWorthNew.as_view(),
        name="pensions_worth_new",
    ),
    path("detailed/", views.TabIncomes.as_view(), name="detailed"),
    path("detailed/incomes/", views.TabIncomes.as_view(), name="detailed_incomes"),
    path("detailed/savings/", views.TabSavings.as_view(), name="detailed_savings"),
    path("detailed/expenses/", views.TabExpenses.as_view(), name="detailed_expenses"),
    path(
        "detailed/expenses/<slug:type_slug>/",
        views.DetailedTable.as_view(),
        {"category": "expenses"},
        name="detailed_type",
    ),
    path("summary/", views.Summary.as_view(), name="summary"),
    path("summary/savings/", views.SummarySavings.as_view(), name="summary_savings"),
    path(
        "summary/savings_and_incomes/",
        views.SummarySavingsAndIncomes.as_view(),
        name="summary_savings_and_incomes",
    ),
    path("summary/expenses/", views.SummaryExpenses.as_view(), name="summary_expenses"),
    path("month/", views.Month.as_view(), name="month"),
    path("month/<str:chart_type>", views.MonthChart.as_view(), name="month_chart"),
    path(
        "month/<date:date>/",
        views.ExpandDayExpenses.as_view(),
        name="expand_day_expenses",
    ),
]
