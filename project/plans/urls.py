from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path(
        'plans/',
        views.Index.as_view(),
        name='index'
    ),
    path(
        'plans/stats/',
        views.Stats.as_view(),
        name='stats'
    ),
    #------------------------------------------------------------------------------------
    #                                                                       expenses plan
    #------------------------------------------------------------------------------------
    path(
        'plans/expenses/',
        views.ExpensesLists.as_view(),
        name='expense_list'
    ),
    path(
        'plans/expenses/new/',
        views.ExpensesNew.as_view(),
        name='expense_new'
    ),
    path(
        'plans/expenses/update/<int:pk>/',
        views.ExpensesUpdate.as_view(),
        name='expense_update'
    ),
    path(
        'plans/expenses/delete/<int:pk>/',
        views.ExpensesDelete.as_view(),
        name='expense_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                         income plan
    #------------------------------------------------------------------------------------
    path(
        'plans/incomes/',
        views.IncomesLists.as_view(),
        name='income_list'
    ),
    path(
        'plans/incomes/new/',
        views.IncomesNew.as_view(),
        name='income_new'
    ),
    path(
        'plans/incomes/update/<int:pk>/',
        views.IncomesUpdate.as_view(),
        name='income_update'
    ),
    path(
        'plans/incomes/delete/<int:pk>/',
        views.IncomesDelete.as_view(),
        name='income_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                         saving plan
    #------------------------------------------------------------------------------------
    path(
        'plans/savings/',
        views.SavingsLists.as_view(),
        name='saving_list'
    ),
    path(
        'plans/savings/new/',
        views.SavingsNew.as_view(),
        name='saving_new'
    ),
    path(
        'plans/savings/update/<int:pk>/',
        views.SavingsUpdate.as_view(),
        name='saving_update'
    ),
    path(
        'plans/savings/delete/<int:pk>/',
        views.SavingsDelete.as_view(),
        name='saving_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                            day plan
    #------------------------------------------------------------------------------------
    path(
        'plans/day/',
        views.DayLists.as_view(),
        name='day_list'
    ),
    path(
        'plans/day/new/',
        views.DayNew.as_view(),
        name='day_new'
    ),
    path(
        'plans/day/update/<int:pk>/',
        views.DayUpdate.as_view(),
        name='day_update'
    ),
    path(
        'plans/day/delete/<int:pk>/',
        views.DayDelete.as_view(),
        name='day_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                      necessary plan
    #------------------------------------------------------------------------------------
    path(
        'plans/necessary/',
        views.NecessaryLists.as_view(),
        name='necessary_list'
    ),
    path(
        'plans/necessary/new/',
        views.NecessaryNew.as_view(),
        name='necessary_new'
    ),
    path(
        'plans/necessary/update/<int:pk>/',
        views.NecessaryUpdate.as_view(),
        name='necessary_update'
    ),
    path(
        'plans/necessary/delete/<int:pk>/',
        views.NecessaryDelete.as_view(),
        name='necessary_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                          copy plans
    #------------------------------------------------------------------------------------
    path(
        'plans/copy/',
        views.CopyPlans.as_view(),
        name='copy'
    ),
]
