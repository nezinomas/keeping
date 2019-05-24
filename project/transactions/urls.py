from django.urls import path

from . import views

app_name = 'transactions'

urlpatterns = [
    path(
        'transactions/',
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
]
