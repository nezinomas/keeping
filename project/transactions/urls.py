from django.urls import path

from . import views

app_name = 'transactions'

urlpatterns = [
    path(
        'transactions/lists/',
        views.lists,
        name='transactions_lists'
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
]
