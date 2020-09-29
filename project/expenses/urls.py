from django.urls import path

from .views import expenses, expenses_type, expenses_name

app_name = 'expenses'

e = [
    path(
        'expenses/',
        expenses.Index.as_view(),
        name='expenses_index'
    ),
    path(
        'expenses/lists/',
        expenses.Lists.as_view(),
        name='expenses_list'
    ),
    path(
        'expenses/lists/<int:month>/',
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
        'ajax/load_expense_name/',
        expenses.load_expense_name,
        name='load_expense_name'
    ),
    path(
        'expenses/reload/',
        expenses.reload,
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
