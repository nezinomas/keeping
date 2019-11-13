from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, reverse
from django.template.loader import render_to_string

from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models
from .lib.calc_day_sum import CalcDaySum


def plans_stats(request):
    ajax_trigger = request.GET.get('ajax_trigger')
    arr = CalcDaySum(request.user.year).plans_stats
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
        context['necessary_list'] = NecessaryLists.as_view()(self.request, as_string=True)
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


#
# Necessary Plan views
#
class NecessaryLists(ListMixin):
    model = models.NecessaryPlan


class NecessaryNew(CreateAjaxMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm


class NecessaryUpdate(UpdateAjaxMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm


# ----------------------------------------------------------------------------
#                                                                   Copy Plans
# ----------------------------------------------------------------------------
@login_required
def copy_plans(request):
    data = {}
    form = forms.CopyPlanForm(data=(request.POST or None))
    if request.method == 'POST':
        if form.is_valid():
            data['form_is_valid'] = True
            form.save()
        else:
            data['form_is_valid'] = False

    context = {
        'form': form,
        'action': 'insert',
        'url': reverse('plans:copy_plans'),
    }

    data['html_form'] = render_to_string(
        template_name='plans/includes/copy_plans_form.html',
        context=context,
        request=request
    )

    return JsonResponse(data)
