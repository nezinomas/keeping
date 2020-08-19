from django.urls import path, register_converter

from ..core import converters
from . import views
from .apps import App_name


app_name = App_name

register_converter(converters.DateConverter, 'date')

urlpatterns = [
    path(
        '',
        views.Index.as_view(),
        name='index'
    ),
    path(
        'bookkeeping/reload/',
        views.ReloadIndex.as_view(),
        name='reload_index'
    ),
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
        'bookkeeping/accounts_worth/reset/<int:pk>/',
        views.AccountsWorthReset.as_view(),
        name='accounts_worth_reset'
    ),
    path(
        'bookkeeping/pensions_worth/new/',
        views.PensionsWorthNew.as_view(),
        name='pensions_worth_new'
    ),
    path(
        'detailed/',
        views.Detailed.as_view(),
        name='detailed'
    ),
    path(
        'summary/',
        views.Summary.as_view(),
        name='summary'
    ),
    path(
        'month/',
        views.Month.as_view(),
        name='month'
    ),
    path(
        'month/reload/',
        views.ReloadMonth.as_view(),
        name='reload_month'
    ),
    path(
        'month/<date:date>/',
        views.ExpandDayExpenses.as_view(),
        name='expand_day_expenses'
    ),
]
