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
        views.expenses_lists,
        name='plans_expenses_list'
    ),
    path(
        'plans/expenses/new/',
        views.expenses_new,
        name='plans_expenses_new'
    ),
    path(
        'plans/expenses/update/<int:pk>/',
        views.expenses_update,
        name='plans_expenses_update'
    ),
    #
    # income plans
    #
    path(
        'plans/incomes/',
        views.incomes_lists,
        name='plans_incomes_list'
    ),
    path(
        'plans/incomes/new/',
        views.incomes_new,
        name='plans_incomes_new'
    ),
    path(
        'plans/incomes/update/<int:pk>/',
        views.incomes_update,
        name='plans_incomes_update'
    ),
    #
    # saving plan
    #
    path(
        'plans/savings/',
        views.savings_lists,
        name='plans_savings_list'
    ),
    path(
        'plans/savings/new/',
        views.savings_new,
        name='plans_savings_new'
    ),
    path(
        'plans/savings/update/<int:pk>/',
        views.savings_update,
        name='plans_savings_update'
    ),
    #
    # day plan
    #
    path(
        'plans/day/',
        views.day_lists,
        name='plans_day_list'
    ),
    path(
        'plans/day/new/',
        views.day_new,
        name='plans_day_new'
    ),
    path(
        'plans/day/update/<int:pk>/',
        views.day_update,
        name='plans_day_update'
    ),
]
