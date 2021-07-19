from django.urls import path

from .apps import App_name
from .views import expenses, expenses_name, expenses_type

app_name = App_name

e = [
    path(
        'expenses/index/',
        expenses.Index.as_view(),
        name='expenses_index'
    ),
    path(
        'expenses/',
        expenses.Lists.as_view(),
        name='expenses_list'
    ),
    path(
        'expenses/<int:month>/',
        expenses.MonthLists.as_view(),
        name='expenses_month_list'
    ),
    path(
        'expenses/new/',
        expenses.New.as_view(),
        name='expenses_new'
    ),
    path(
        'expenses/update/<int:pk>/',
        expenses.Update.as_view(),
        name='expenses_update'
    ),
    path(
        'expenses/delete/<int:pk>/',
        expenses.Delete.as_view(),
        name='expenses_delete'
    ),
    path(
        'ajax/load_expense_name/',
        expenses.LoadExpenseName.as_view(),
        name='load_expense_name'
    ),
    path(
        'expenses/reload/',
        expenses.ReloadExpenses.as_view(),
        name='reload_expenses'
    ),
    path(
        'expenses/search/',
        expenses.Search.as_view(),
        name='expenses_search'
    )
]

e_type = [
    path(
        'expenses/type/new/',
        expenses_type.New.as_view(),
        name='expenses_type_new'
    ),
    path(
        'expenses/type/update/<int:pk>/',
        expenses_type.Update.as_view(),
        name='expenses_type_update'
    ),
]

e_name = [
    path(
        'expenses/name/new/',
        expenses_name.New.as_view(),
        name='expenses_name_new'
    ),
    path(
        'expenses/name/update/<int:pk>/',
        expenses_name.Update.as_view(),
        name='expenses_name_update'
    ),
]

urlpatterns = []
urlpatterns += e
urlpatterns += e_type
urlpatterns += e_name
