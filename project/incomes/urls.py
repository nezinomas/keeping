from django.urls import path

from . import views

app_name = 'incomes'

urlpatterns = [
    path(
        'incomes/',
        views.lists,
        name='incomes_list'
    ),
    path(
        'incomes/new/',
        views.new,
        name='incomes_new'
    ),
    path(
        'incomes/update/<int:pk>/',
        views.update,
        name='incomes_update'
    ),
    path(
        'incomes/type/',
        views.type_lists,
        name='incomes_type_list'
    ),
    path(
        'incomes/type/new/',
        views.type_new,
        name='incomes_type_new'
    ),
    path(
        'incomes/type/update/<int:pk>/',
        views.type_update,
        name='incomes_type_update'
    ),
]
