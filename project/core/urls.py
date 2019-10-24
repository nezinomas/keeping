from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('core/', views.index, name='core_index'),
    path(
        'set/year/<int:year>/<str:view_name>/',
        views.set_year,
        name='set_year'),
    path(
        'set/month/<int:month>/<str:view_name>/',
        views.set_month,
        name='set_month'),
    path(
        'set/balances/',
        views.regenerate_balances,
        name='regenerate_balances'),
    path(
        'set/balances/<int:year>/',
        views.regenerate_balances_current_year,
        name='regenerate_balances_current_year'),
]
