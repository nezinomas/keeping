from django.urls import path

from . import views

app_name = 'bookkeeping'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
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
]
