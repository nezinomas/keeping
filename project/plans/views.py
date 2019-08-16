from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template.loader import render_to_string

from ..core.mixins.crud import CreateAjaxMixin, ListMixin, UpdateAjaxMixin
from . import forms, models
from .lib.day_sum import DaySum


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


@login_required()
def plans_index(request):
    context = {
        'expenses_list': ExpensesLists.as_view()(request, as_string=True),
        'incomes_list': IncomesLists.as_view()(request, as_string=True),
        'savings_list': SavingsLists.as_view()(request, as_string=True),
        'day_list': DayLists.as_view()(request, as_string=True),
        'plans_stats': plans_stats(request)
    }
    return render(request, 'plans/plans_list.html', context)


#
# Expense Plan views
#
class ExpensesLists(ListMixin):
    model = models.ExpensePlan


class ExpensesNew(CreateAjaxMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm


class ExpensesUpdate(UpdateAjaxMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm


#
# Income Plan views
#
class IncomesLists(ListMixin):
    model = models.IncomePlan


class IncomesNew(CreateAjaxMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm


class IncomesUpdate(UpdateAjaxMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm


#
# Saving Plan views
#
class SavingsLists(ListMixin):
    model = models.SavingPlan


class SavingsNew(CreateAjaxMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm


class SavingsUpdate(UpdateAjaxMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm


#
# Day Plan views
#
class DayLists(ListMixin):
    model = models.DayPlan


class DayNew(CreateAjaxMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm


class DayUpdate(UpdateAjaxMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm
