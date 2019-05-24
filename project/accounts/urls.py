from django.urls import path

from . import views

app_name = 'accounts'


urlpatterns = [
    path(
        'accounts/',
        views.lists,
        name='accounts_list'
    ),
    path(
        'accounts/new/',
        views.new,
        name='accounts_new'
    ),
    path(
        'accounts/update/<int:pk>/',
        views.update,
        name='accounts_update'
    ),
    path(
        'ajax/load_to_account/',
        views.load_to_account,
        name='load_to_account'
    )
]
