from django.shortcuts import render
from django.template.loader import render_to_string

from ..core.mixins.crud import CreateAjaxMixin, ListMixin, UpdateAjaxMixin, IndexMixin
from . import forms, models
from .lib.day_sum import DaySum


def plans_stats(request):
    ajax_trigger = request.GET.get('ajax_trigger')
    arr = DaySum(request.user.profile.year).plans_stats
    t_name = 'plans/includes/plans_stats.html'
    c = {'items': arr}

    if ajax_trigger:
        return render(template_name=t_name, context=c, request=request)
    else:
        return render_to_string(template_name=t_name, context=c, request=request)


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['expenses_list'] = ExpensesLists.as_view()(self.request, as_string=True)
        context['incomes_list'] = IncomesLists.as_view()(self.request, as_string=True)
        context['savings_list'] = SavingsLists.as_view()(self.request, as_string=True)
        context['day_list'] = DayLists.as_view()(self.request, as_string=True)
        context['plans_stats'] = plans_stats(self.request)

        return context


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
