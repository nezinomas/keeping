from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path("", views.TabDay.as_view(), name="index"),
    path("expenses/", views.TabExpenses.as_view(), name="tab_expenses"),
    path("expenses/new/", views.ExpensesNew.as_view(), name="expense_new"),
    path(
        "expenses/update/<int:year>/<int:expense_type_id>/",
        views.ExpensesUpdate.as_view(),
        name="expense_update",
    ),
    path(
        "expenses/delete/<int:year>/<int:expense_type_id>/",
        views.ExpensesDelete.as_view(),
        name="expense_delete",
    ),
    path("incomes/", views.TabIncomes.as_view(), name="tab_incomes"),
    path("incomes/new/", views.IncomesNew.as_view(), name="income_new"),
    path(
        "incomes/update/<int:year>/<int:income_type_id>/",
        views.IncomesUpdate.as_view(),
        name="income_update",
    ),
    path(
        "incomes/delete/<int:year>/<int:income_type_id>/",
        views.IncomesDelete.as_view(),
        name="income_delete",
    ),
    path("savings/", views.TabSavings.as_view(), name="tab_savings"),
    path("savings/new/", views.SavingsNew.as_view(), name="saving_new"),
    path(
        "savings/update/<int:year>/<int:saving_type_id>/",
        views.SavingsUpdate.as_view(),
        name="saving_update",
    ),
    path(
        "savings/delete/<int:year>/<int:saving_type_id>/",
        views.SavingsDelete.as_view(),
        name="saving_delete",
    ),
    path("day/", views.TabDay.as_view(), name="tab_day"),
    path("day/new/", views.DayNew.as_view(), name="day_new"),
    path("day/update/<int:year>/", views.DayUpdate.as_view(), name="day_update"),
    path("day/delete/<int:year>/", views.DayDelete.as_view(), name="day_delete"),
    path("necessary/new/", views.NecessaryNew.as_view(), name="necessary_new"),
    path(
        "necessary/update/<int:year>/<int:expense_type_id>/<path:title>/",
        views.NecessaryUpdate.as_view(),
        name="necessary_update",
    ),
    path(
        "necessary/delete/<int:year>/<int:expense_type_id>/<path:title>/",
        views.NecessaryDelete.as_view(),
        name="necessary_delete",
    ),
    path("copy/", views.CopyPlans.as_view(), name="copy"),
]
