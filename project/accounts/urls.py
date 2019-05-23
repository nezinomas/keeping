from django.urls import path

from . import views

app_name = 'accounts'


urlpatterns = [
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
]
