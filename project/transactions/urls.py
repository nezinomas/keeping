from django.urls import path

from . import views

app_name = 'transactions'

urlpatterns = [
    path(
        'transactions/',
        views.index,
        name='transactions_index'
    ),
    path(
        'transactions/lists/',
        views.lists,
        name='transactions_list'
    ),
    path(
        'transactions/new/',
        views.new,
        name='transactions_new'
    ),
    path(
        'transactions/update/<int:pk>/',
        views.update,
        name='transactions_update'
    ),
    path(
        'savings_close/new/',
        views.savings_close_new,
        name='savings_close_new'
    ),
    path(
        'savings_close/update/<int:pk>/',
        views.savings_close_update,
        name='savings_close_update'
    ),
    path(
        'savings_change/new/',
        views.savings_change_new,
        name='savings_change_new'
    ),
    path(
        'savings_change/update/<int:pk>/',
        views.savings_change_update,
        name='savings_change_update'
    ),
]
