from django.urls import path
from . import views
from .apps import App_name

app_name = App_name


urlpatterns = [
    path(
        'set/year/<int:year>/',
        views.set_year,
        name='set_year'),
    path(
        'set/month/<int:month>/',
        views.set_month,
        name='set_month'),
    path(
        'set/balances/',
        views.RegenerateBalances.as_view(),
        name='regenerate_balances'),
]
