from django.shortcuts import get_object_or_404, render, reverse
from django.template.loader import render_to_string

from ..core.mixins.save_data_mixin import SaveDataMixin
from .forms import ExpensePlanForm, IncomePlanForm
from .models import DayPlan, ExpensePlan, IncomePlan, SavingPlan


def plans_index(request):
    form = ExpensePlanForm()
    context = {
        'expenses_list': expenses_lists(request),
        'incomes_list': income_lists(request),
        'form': form
    }
    return render(request, 'plans/plans_list.html', context)


#
# Expense Plan views
#
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
    form = ExpensePlanForm(request.POST or None)
    context = {
        'url': reverse('plans:plans_expenses_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _expense_json_response(request, obj)


def expenses_update(request, pk):
    object = get_object_or_404(ExpensePlan, pk=pk)
    form = ExpensePlanForm(request.POST or None, instance=object)
    url = reverse(
        'plans:plans_expenses_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _expense_json_response(request, obj)


#
# Income Plan views
#
def _incomes_json_response(request, obj):
    obj.form_template = 'plans/includes/partial_incomes_form.html'
    obj.items_template = 'plans/includes/partial_incomes_list.html'

    obj.items_template_var_name = 'incomes_list'
    obj.items = IncomePlan.objects.items(request.user.profile.year)

    return obj.GenJsonResponse()


def income_lists(request):
    qs = IncomePlan.objects.items(request.user.profile.year)

    return render_to_string(
        'plans/includes/partial_incomes_list.html',
        {'incomes_list': qs},
        request,
    )


def income_new(request):
    form = IncomePlanForm(request.POST or None)
    context = {
        'url': reverse('plans:plans_incomes_new'),
        'action': 'insert'
    }

    obj = SaveDataMixin(request, context, form)

    return _incomes_json_response(request, obj)


def income_update(request, pk):
    object = get_object_or_404(IncomePlan, pk=pk)
    form = IncomePlanForm(request.POST or None, instance=object)
    url = reverse(
        'plans:plans_incomes_update',
        kwargs={
            'pk': pk
        }
    )
    context = {'url': url, 'action': 'update'}

    obj = SaveDataMixin(request, context, form)

    return _incomes_json_response(request, obj)


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
