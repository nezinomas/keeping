from django.urls import path

from . import views

app_name = 'transactions'

urlpatterns = [
    path(
        'transactions/',
        views.Index.as_view(),
        name='transactions_index'
    ),
    path(
        'transactions/lists/',
        views.Lists.as_view(),
        name='transactions_list'
    ),
    path(
        'transactions/new/',
        views.New.as_view(),
        name='transactions_new'
    ),
    path(
        'transactions/update/<int:pk>/',
        views.Update.as_view(),
        name='transactions_update'
    ),
    path(
        'savings_close/new/',
        views.SavingsCloseNew.as_view(),
        name='savings_close_new'
    ),
    path(
        'savings_close/update/<int:pk>/',
        views.SavingsCloseUpdate.as_view(),
        name='savings_close_update'
    ),
    path(
        'savings_change/new/',
        views.SavingsChangeNew.as_view(),
        name='savings_change_new'
    ),
    path(
        'savings_change/update/<int:pk>/',
        views.SavingsChangeUpdate.as_view(),
        name='savings_change_update'
    ),
    path(
        'ajax/load_saving_type/',
        views.load_saving_type,
        name='load_saving_type'
    ),
]
