from django.urls import path

from .views import expenses, expenses_type, expenses_name

app_name = 'expenses'

e = [
    path(
        'expenses/',
        expenses.lists,
        name='expenses_list'
    ),
    path(
        'expenses/new/',
        expenses.new,
        name='expenses_new'
    ),
    path(
        'expenses/update/<int:pk>/',
        expenses.update,
        name='expenses_update'
    ),
    path(
        'ajax/load_expense_name/',
        expenses.load_expense_name,
        name='load_expense_name'
    )
]

e_type = [
    path(
        'expenses/type/new/',
        expenses_type.new,
        name='expenses_type_new'
    ),
    path(
        'expenses/type/update/<int:pk>/',
        expenses_type.update,
        name='expenses_type_update'
    ),
]

e_name = [
    path(
        'expenses/name/',
        expenses_name.lists,
        name='expenses_name_list'
    ),
    path(
        'expenses/name/new/',
        expenses_name.new,
        name='expenses_name_new'
    ),
    path(
        'expenses/name/update/<int:pk>/',
        expenses_name.update,
        name='expenses_name_update'
    ),
]

urlpatterns = []
urlpatterns += e
urlpatterns += e_type
urlpatterns += e_name
