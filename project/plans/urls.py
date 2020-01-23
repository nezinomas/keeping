from django.urls import path

from . import views

app_name = 'plans'

urlpatterns = [
    path(
        'plans/',
        views.Index.as_view(),
        name='plans_index'
    ),
    #
    # expenses plan
    #
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
    #
    # income plans
    #
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
    #
    # saving plan
    #
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
    #
    # day plan
    #
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
    #
    # necessary plan
    #
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
    #
    # copy plans
    #
    path(
        'plans/copy/',
        views.copy_plans,
        name='copy_plans'
    ),
]
