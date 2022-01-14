from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path(
        'plans/',
        views.Index.as_view(),
        name='plans_index'
    ),
    #------------------------------------------------------------------------------------
    #                                                                       expenses plan
    #------------------------------------------------------------------------------------
    path(
        'plans/expenses/',
        views.ExpensesLists.as_view(),
        name='expenses_plan_list'
    ),
    path(
        'plans/expenses/new/',
        views.ExpensesNew.as_view(),
        name='expenses_plan_new'
    ),
    path(
        'plans/expenses/update/<int:pk>/',
        views.ExpensesUpdate.as_view(),
        name='expenses_plan_update'
    ),
    path(
        'plans/expenses/delete/<int:pk>/',
        views.ExpensesDelete.as_view(),
        name='expenses_plan_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                         income plan
    #------------------------------------------------------------------------------------
    path(
        'plans/incomes/',
        views.IncomesLists.as_view(),
        name='incomes_plan_list'
    ),
    path(
        'plans/incomes/new/',
        views.IncomesNew.as_view(),
        name='incomes_plan_new'
    ),
    path(
        'plans/incomes/update/<int:pk>/',
        views.IncomesUpdate.as_view(),
        name='incomes_plan_update'
    ),
    path(
        'plans/incomes/delete/<int:pk>/',
        views.IncomesDelete.as_view(),
        name='incomes_plan_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                         saving plan
    #------------------------------------------------------------------------------------
    path(
        'plans/savings/',
        views.SavingsLists.as_view(),
        name='savings_plan_list'
    ),
    path(
        'plans/savings/new/',
        views.SavingsNew.as_view(),
        name='savings_plan_new'
    ),
    path(
        'plans/savings/update/<int:pk>/',
        views.SavingsUpdate.as_view(),
        name='savings_plan_update'
    ),
    path(
        'plans/savings/delete/<int:pk>/',
        views.SavingsDelete.as_view(),
        name='savings_plan_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                            day plan
    #------------------------------------------------------------------------------------
    path(
        'plans/day/',
        views.DayLists.as_view(),
        name='days_plan_list'
    ),
    path(
        'plans/day/new/',
        views.DayNew.as_view(),
        name='days_plan_new'
    ),
    path(
        'plans/day/update/<int:pk>/',
        views.DayUpdate.as_view(),
        name='days_plan_update'
    ),
    path(
        'plans/day/delete/<int:pk>/',
        views.DayDelete.as_view(),
        name='days_plan_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                      necessary plan
    #------------------------------------------------------------------------------------
    path(
        'plans/necessary/',
        views.NecessaryLists.as_view(),
        name='necessarys_plan_list'
    ),
    path(
        'plans/necessary/new/',
        views.NecessaryNew.as_view(),
        name='necessarys_plan_new'
    ),
    path(
        'plans/necessary/update/<int:pk>/',
        views.NecessaryUpdate.as_view(),
        name='necessarys_plan_update'
    ),
    path(
        'plans/reload_plan_stats/',
        views.plans_stats,
        name='reload_plan_stats'
    ),
    path(
        'plans/necessary/delete/<int:pk>/',
        views.NecessaryDelete.as_view(),
        name='necessarys_plan_delete'
    ),
    #------------------------------------------------------------------------------------
    #                                                                          copy plans
    #------------------------------------------------------------------------------------
    path(
        'plans/copy/',
        views.CopyPlans.as_view(),
        name='copy_plans'
    ),
]
