from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.save_data_mixin import SaveDataMixin
from .models import DayPlan, ExpensePlan, IncomePlan, SavingPlan


def plans_index(request):
    context = {
        'expenses_list': expenses_lists(request)
    }
    return render(request, 'plans/plans_list.html', context)


# Expense Plan views

def _expense_json_response(request, obj):
    obj.form_template = 'plans/includes/partial_expenses_form.html'
    obj.items_template = 'plans/includes/partial_expenses_list.html'

    obj.items_template_var_name = 'expenses_list'
    obj.items = ExpensePlan.objects.items(request.user.profile.year)

    return obj.GenJsonResponse()


def expenses_lists(request):
    qs = ExpensePlan.objects.items(request.user.profile.year)
    return render_to_string(
        'plans/includes/partial_expenses_list.html',
        {'expenses_list': qs},
        request,
    )


def expenses_new(request):
    pass


def expenses_update(request, pk):
    pass


def income_lists(request):
    pass


def income_new(request):
    pass


def income_update(request, pk):
    pass


def savings_lists(request):
    pass


def savings_new(request):
    pass


def savings_update(request, pk):
    pass


def day_lists(request):
    pass


def day_new(request):
    pass


def day_update(request, pk):
    pass
