from django.urls import path

from . import views

app_name = 'plans'

urlpatterns = [
    path(
        'plans/',
        views.plans_index,
        name='plans_index'
    ),
    #
    # expenses plan
    #
    path(
        'plans/expenses/',
        views.ExpensesLists.as_view(),
        name='expenses_plans_list'
    ),
    path(
        'plans/expenses/new/',
        views.ExpensesNew.as_view(),
        name='expenses_plans_new'
    ),
    path(
        'plans/expenses/update/<int:pk>/',
        views.ExpensesUpdate.as_view(),
        name='expenses_plans_update'
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
        name='savings_plans_list'
    ),
    path(
        'plans/savings/new/',
        views.SavingsNew.as_view(),
        name='savings_plans_new'
    ),
    path(
        'plans/savings/update/<int:pk>/',
        views.SavingsUpdate.as_view(),
        name='savings_plans_update'
    ),
    #
    # day plan
    #
    path(
        'plans/day/',
        views.DayLists.as_view(),
        name='days_plans_list'
    ),
    path(
        'plans/day/new/',
        views.DayNew.as_view(),
        name='days_plans_new'
    ),
    path(
        'plans/day/update/<int:pk>/',
        views.DayUpdate.as_view(),
        name='days_plans_update'
    ),
    path(
        'plans/reload_plans_stats/',
        views.plans_stats,
        name='reload_plans_stats'
    )
]
