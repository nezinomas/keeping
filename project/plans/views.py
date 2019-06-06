from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template.loader import render_to_string

from ..core.mixins.crud_views_mixin import CrudMixin, CrudMixinSettings
from .forms import DayPlanForm, ExpensePlanForm, IncomePlanForm, SavingPlanForm
from .lib.day_sum import DaySum
from .models import DayPlan, ExpensePlan, IncomePlan, SavingPlan


@login_required()
def plans_stats(request):
    ajax_trigger = request.GET.get('ajax_trigger')
    arr = DaySum(request.user.profile.year).plans_stats
    t_name = 'plans/includes/partial_plans_stats.html'
    c = {'items': arr}

    if ajax_trigger:
        return render(template_name=t_name, context=c, request=request)
    else:
        return render_to_string(template_name=t_name, context=c, request=request)


#
# Expense Plan views
#
def expenses_settings():
    obj = CrudMixinSettings()

    obj.model = ExpensePlan

    obj.form = ExpensePlanForm
    obj.form_template = 'plans/includes/partial_expenses_form.html'

    obj.items_template = 'plans/includes/partial_expenses_list.html'
    obj.items_template_main = 'plans/plans_list.html'

    obj.url_new = 'plans:plans_expenses_new'
    obj.url_update = 'plans:plans_expenses_update'

    return obj


@login_required()
def plans_index(request):
    context = {
        'expenses_list': expenses_lists(request),
        'incomes_list': incomes_lists(request),
        'savings_list': savings_lists(request),
        'day_list': day_lists(request),
        'plans_stats': plans_stats(request)
    }
    return CrudMixin(request, expenses_settings()).lists_as_html(context)


@login_required()
def expenses_lists(request):
    return CrudMixin(request, expenses_settings()).lists_as_str()


@login_required()
def expenses_new(request):
    return CrudMixin(request, expenses_settings()).new()


@login_required()
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


@login_required()
def incomes_lists(request):
    return CrudMixin(request, incomes_settings()).lists_as_str()


@login_required()
def incomes_new(request):
    return CrudMixin(request, incomes_settings()).new()


@login_required()
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


@login_required()
def savings_lists(request):
    return CrudMixin(request, savings_settings()).lists_as_str()


@login_required()
def savings_new(request):
    return CrudMixin(request, savings_settings()).new()


@login_required()
def savings_update(request, pk):
    settings = savings_settings()
    settings.item_id = pk

    return CrudMixin(request, settings).update()


#
# Day Plan views
#
def day_settings():
    obj = CrudMixinSettings()

    obj.model = DayPlan

    obj.form = DayPlanForm
    obj.form_template = 'plans/includes/partial_day_form.html'

    obj.items_template = 'plans/includes/partial_day_list.html'

    obj.url_new = 'plans:plans_day_new'
    obj.url_update = 'plans:plans_day_update'

    return obj


@login_required()
def day_lists(request):
    return CrudMixin(request, day_settings()).lists_as_str()


@login_required()
def day_new(request):
    return CrudMixin(request, day_settings()).new()


@login_required()
def day_update(request, pk):
    settings = day_settings()
    settings.item_id = pk

    return CrudMixin(request, settings).update()
