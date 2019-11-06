from django.urls import path

from . import views

app_name = 'bookkeeping'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('month/', views.Month.as_view(), name='month'),
    path(
        'bookkeeping/savings_worth/new/',
        views.SavingsWorthNew.as_view(),
        name='savings_worth_new'
    ),
    path(
        'bookkeeping/accounts_worth/new/',
        views.AccountsWorthNew.as_view(),
        name='accounts_worth_new'
    ),
    path(
        'bookkeeping/pensions_worth/new/',
        views.PensionsWorthNew.as_view(),
        name='pensions_worth_new'
    ),
    path(
        'month/reload/',
        views.reload_month,
        name='reload_month'
    ),
]
