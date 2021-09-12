from django.urls import path

from . import views
from .apps import App_name

app_name = App_name


urlpatterns = [
    path(
        'accounts/',
        views.Lists.as_view(),
        name='accounts_list'
    ),
    path(
        'accounts/new/',
        views.New.as_view(),
        name='accounts_new'
    ),
    path(
        'accounts/update/<int:pk>/',
        views.Update.as_view(),
        name='accounts_update'
    ),
    path(
        'ajax/load_to_account/',
        views.LoadAccount.as_view(),
        name='load_to_account'
    )
]
