from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from .forms import ExpensePlanForm, IncomePlanForm, SavingPlanForm
from .models import DayPlan, ExpensePlan, IncomePlan, SavingPlan


def plans_index(request):
    form = ExpensePlanForm()
    context = {
        'form': form,
        'expenses_list': expenses_lists(request),
        'incomes_list': incomes_lists(request),
        'savings_list': savings_lists(request),
    }
    return render(request, 'plans/plans_list.html', context)


#
# Expense Plan views
#
def expenses_settings():
    obj = CrudMixinSettings()

    obj.model = ExpensePlan

    obj.form = ExpensePlanForm
    obj.form_template = 'plans/includes/partial_expenses_form.html'

    obj.items_template = 'plans/includes/partial_expenses_list.html'

    obj.url_new = 'plans:plans_expenses_new'
    obj.url_update = 'plans:plans_expenses_update'

    return obj


def expenses_lists(request):
    return CrudMixin(request, expenses_settings()).lists_as_str()


def expenses_new(request):
    return CrudMixin(request, expenses_settings()).new()


def expenses_update(request, pk):
    settings = expenses_settings()
    settings.item_id = pk

    return CrudMixin(request, settings).update()


#
# Income Plan views
#
def incomes_settings():
    obj = CrudMixinSettings()

    obj.model = IncomePlan

    obj.form = IncomePlanForm
    obj.form_template = 'plans/includes/partial_incomes_form.html'

    obj.items_template = 'plans/includes/partial_incomes_list.html'

    obj.url_new = 'plans:plans_incomes_new'
    obj.url_update = 'plans:plans_incomes_update'

    return obj


def incomes_lists(request):
    return CrudMixin(request, incomes_settings()).lists_as_str()


def incomes_new(request):
    return CrudMixin(request, incomes_settings()).new()


def incomes_update(request, pk):
    settings = incomes_settings()
    settings.item_id = pk

    return CrudMixin(request, settings).update()


#
# Saving Plan views
#
def savings_settings():
    obj = CrudMixinSettings()

    obj.model = SavingPlan

    obj.form = SavingPlanForm
    obj.form_template = 'plans/includes/partial_savings_form.html'

    obj.items_template = 'plans/includes/partial_savings_list.html'

    obj.url_new = 'plans:plans_savings_new'
    obj.url_update = 'plans:plans_savings_update'

    return obj


def savings_lists(request):
    return CrudMixin(request, savings_settings()).lists_as_str()


def savings_new(request):
    return CrudMixin(request, savings_settings()).new()


def savings_update(request, pk):
    settings = incomes_settings()
    settings.item_id = pk

    return CrudMixin(request, settings).update()


def day_lists(request):
    pass


def day_new(request):
    pass


def day_update(request, pk):
    pass
