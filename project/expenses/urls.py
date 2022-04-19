from django.urls import path

from .apps import App_name
from .views import expenses, expenses_name, expenses_type

app_name = App_name


urlpatterns = [
    path(
        'expenses/index/',
        expenses.Index.as_view(),
        name='index'
    ),
    path(
        'expenses/',
        expenses.Lists.as_view(),
        name='list'
    ),
    path(
        'expenses/new/',
        expenses.New.as_view(),
        name='new'
    ),
    path(
        'expenses/update/<int:pk>/',
        expenses.Update.as_view(),
        name='update'
    ),
    path(
        'expenses/delete/<int:pk>/',
        expenses.Delete.as_view(),
        name='delete'
    ),
    path(
        'expenses/load_expense_name/',
        expenses.LoadExpenseName.as_view(),
        name='load_expense_name'
    ),
    path(
        'expenses/search/',
        expenses.Search.as_view(),
        name='search'
    ),
    path(
        'expenses/type/new/',
        expenses_type.New.as_view(),
        name='type_new'
    ),
    path(
        'expenses/type/update/<int:pk>/',
        expenses_type.Update.as_view(),
        name='type_update'
    ),
    path(
        'expenses/name/new/',
        expenses_name.New.as_view(),
        name='name_new'
    ),
    path(
        'expenses/name/update/<int:pk>/',
        expenses_name.Update.as_view(),
        name='name_update'
    ),
]
