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
        'set/accounts/',
        views.regenerate_accounts_balance,
        name='regenerate_accounts'),
    path(
        'set/accounts/<int:year>/',
        views.regenerate_accounts_balance_current_year,
        name='regenerate_accounts_current_year'),
    path(
        'set/savings/',
        views.regenerate_savings_balance,
        name='regenerate_savings'),
    path(
        'set/savings/<int:year>/',
        views.regenerate_savings_balance_current_year,
        name='regenerate_savings_current_year'),
]
