from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("stats/", views.Stats.as_view(), name="stats"),
    # ------------------------------------------------------------------------------------
    #                                                                       expenses plan
    # ------------------------------------------------------------------------------------
    path("expenses/", views.ExpensesLists.as_view(), name="expense_list"),
    path("expenses/new/", views.ExpensesNew.as_view(), name="expense_new"),
    path(
        "expenses/update/<int:pk>/",
        views.ExpensesUpdate.as_view(),
        name="expense_update",
    ),
    path(
        "expenses/delete/<int:pk>/",
        views.ExpensesDelete.as_view(),
        name="expense_delete",
    ),
    # ------------------------------------------------------------------------------------
    #                                                                         income plan
    # ------------------------------------------------------------------------------------
    path("incomes/", views.IncomesLists.as_view(), name="income_list"),
    path("incomes/new/", views.IncomesNew.as_view(), name="income_new"),
    path(
        "incomes/update/<int:pk>/", views.IncomesUpdate.as_view(), name="income_update"
    ),
    path(
        "incomes/delete/<int:pk>/", views.IncomesDelete.as_view(), name="income_delete"
    ),
    # ------------------------------------------------------------------------------------
    #                                                                         saving plan
    # ------------------------------------------------------------------------------------
    path("savings/", views.SavingsLists.as_view(), name="saving_list"),
    path("savings/new/", views.SavingsNew.as_view(), name="saving_new"),
    path(
        "savings/update/<int:pk>/", views.SavingsUpdate.as_view(), name="saving_update"
    ),
    path(
        "savings/delete/<int:pk>/", views.SavingsDelete.as_view(), name="saving_delete"
    ),
    # ------------------------------------------------------------------------------------
    #                                                                            day plan
    # ------------------------------------------------------------------------------------
    path("day/", views.DayLists.as_view(), name="day_list"),
    path("day/new/", views.DayNew.as_view(), name="day_new"),
    path("day/update/<int:pk>/", views.DayUpdate.as_view(), name="day_update"),
    path("day/delete/<int:pk>/", views.DayDelete.as_view(), name="day_delete"),
    # ------------------------------------------------------------------------------------
    #                                                                      necessary plan
    # ------------------------------------------------------------------------------------
    path("necessary/", views.NecessaryLists.as_view(), name="necessary_list"),
    path("necessary/new/", views.NecessaryNew.as_view(), name="necessary_new"),
    path(
        "necessary/update/<int:pk>/",
        views.NecessaryUpdate.as_view(),
        name="necessary_update",
    ),
    path(
        "necessary/delete/<int:pk>/",
        views.NecessaryDelete.as_view(),
        name="necessary_delete",
    ),
    # ------------------------------------------------------------------------------------
    #                                                                          copy plans
    # ------------------------------------------------------------------------------------
    path("copy/", views.CopyPlans.as_view(), name="copy"),
]
