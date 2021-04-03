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
        'transactions/delete/<int:pk>/',
        views.Delete.as_view(),
        name='transactions_delete'
    ),
    path(
        'savings_close/new/',
        views.SavingsCloseNew.as_view(),
        name='savings_close_new'
    ),
    path(
        'savings_close/lists/',
        views.SavingsCloseLists.as_view(),
        name='savings_close_list'
    ),
    path(
        'savings_close/update/<int:pk>/',
        views.SavingsCloseUpdate.as_view(),
        name='savings_close_update'
    ),
    path(
        'savings_close/delete/<int:pk>/',
        views.SavingsCloseDelete.as_view(),
        name='savings_close_delete'
    ),
    path(
        'savings_change/new/',
        views.SavingsChangeNew.as_view(),
        name='savings_change_new'
    ),
    path(
        'savings_change/lists/',
        views.SavingsChangeLists.as_view(),
        name='savings_change_list'
    ),
    path(
        'savings_change/update/<int:pk>/',
        views.SavingsChangeUpdate.as_view(),
        name='savings_change_update'
    ),
    path(
        'savings_change/delete/<int:pk>/',
        views.SavingsChangeDelete.as_view(),
        name='savings_change_delete'
    ),
    path(
        'ajax/load_saving_type/',
        views.load_saving_type,
        name='load_saving_type'
    ),
]
