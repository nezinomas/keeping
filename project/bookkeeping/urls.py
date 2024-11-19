from django.urls import path, register_converter

from ..core import converters
from . import views
from .apps import App_name

app_name = App_name

register_converter(converters.DateConverter, "date")

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("bookkeeping/accounts/", views.Accounts.as_view(), name="accounts"),
    path(
        "bookkeeping/accounts_worth/new/",
        views.AccountsWorthNew.as_view(),
        name="accounts_worth_new",
    ),
    path("bookkeeping/savings/", views.Savings.as_view(), name="savings"),
    path(
        "bookkeeping/savings_worth/new/",
        views.SavingsWorthNew.as_view(),
        name="savings_worth_new",
    ),
    path("bookkeeping/pensions/", views.Pensions.as_view(), name="pensions"),
    path(
        "bookkeeping/pensions_worth/new/",
        views.PensionsWorthNew.as_view(),
        name="pensions_worth_new",
    ),
    path("bookkeeping/wealth/", views.Wealth.as_view(), name="wealth"),
    path("bookkeeping/forecast/", views.Forecast.as_view(), name="forecast"),
    path("bookkeeping/no_incomes/", views.NoIncomes.as_view(), name="no_incomes"),
    path("detailed/", views.Detailed.as_view(), name="detailed"),
    path("summary/", views.Summary.as_view(), name="summary"),
    path("summary/savings/", views.SummarySavings.as_view(), name="summary_savings"),
    path(
        "summary/savings_and_incomes/",
        views.SummarySavingsAndIncomes.as_view(),
        name="summary_savings_and_incomes",
    ),
    path("summary/expenses/", views.SummaryExpenses.as_view(), name="summary_expenses"),
    path("month/", views.Month.as_view(), name="month"),
    path(
        "month/<date:date>/",
        views.ExpandDayExpenses.as_view(),
        name="expand_day_expenses",
    ),
]
