from django.urls import path

from .views import expenses, expenses_name, expenses_sub_name

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
        'expenses/<int:pk>/update/',
        expenses.update,
        name='expenses_update'
    ),
    path(
        'expenses/<int:pk>/delete/',
        expenses.delete,
        name='expenses_delete'
    ),
    path(
        'ajax/load_expense_name/',
        expenses.load_sub_categories,
        name='load_sub_categories'
    )
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
        'expenses/name/<int:pk>/update/',
        expenses_name.update,
        name='expenses_name_update'
    ),
    path(
        'expenses/name/<int:pk>/delete/',
        expenses_name.delete,
        name='expenses_name_delete'
    ),
]

e_sub_name = [
    path(
        'expenses/subname/',
        expenses_sub_name.lists,
        name='expenses_sub_name_list'
    ),
    path(
        'expenses/subname/new/',
        expenses_sub_name.new,
        name='expenses_sub_name_new'
    ),
    path(
        'expenses/subname/<int:pk>/update/',
        expenses_sub_name.update,
        name='expenses_sub_name_update'
    ),
    path(
        'expenses/subname/<int:pk>/delete/',
        expenses_sub_name.delete,
        name='expenses_sub_name_delete'
    ),
]

urlpatterns = []
urlpatterns += e
urlpatterns += e_name
urlpatterns += e_sub_name
