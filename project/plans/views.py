from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, reverse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin, IndexMixin,
                                 ListMixin, UpdateAjaxMixin)
from . import forms, models
from .lib.calc_day_sum import CalcDaySum


def plans_stats(request):
    ajax_trigger = request.GET.get('ajax_trigger')
    arr = CalcDaySum(request.user.year).plans_stats
    t_name = 'plans/includes/plans_stats.html'
    c = {'items': arr}

    if ajax_trigger:
        return render(template_name=t_name, context=c, request=request)

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


# ---------------------------------------------------------------------------------------
#                                                                           Expense Plans
# ---------------------------------------------------------------------------------------
class ExpensesLists(ListMixin):
    model = models.ExpensePlan


class ExpensesNew(CreateAjaxMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm


class ExpensesUpdate(UpdateAjaxMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm


class ExpensesDelete(DeleteAjaxMixin):
    model = models.ExpensePlan


# ---------------------------------------------------------------------------------------
#                                                                            Income Plans
# ---------------------------------------------------------------------------------------
class IncomesLists(ListMixin):
    model = models.IncomePlan


class IncomesNew(CreateAjaxMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm


class IncomesUpdate(UpdateAjaxMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm


class IncomesDelete(DeleteAjaxMixin):
    model = models.IncomePlan


# ---------------------------------------------------------------------------------------
#                                                                            Saving Plans
# ---------------------------------------------------------------------------------------
class SavingsLists(ListMixin):
    model = models.SavingPlan


class SavingsNew(CreateAjaxMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm


class SavingsUpdate(UpdateAjaxMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm


class SavingsDelete(DeleteAjaxMixin):
    model = models.SavingPlan


# ---------------------------------------------------------------------------------------
#                                                                               Day Plans
# ---------------------------------------------------------------------------------------
class DayLists(ListMixin):
    model = models.DayPlan


class DayNew(CreateAjaxMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm


class DayUpdate(UpdateAjaxMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm


class DayDelete(DeleteAjaxMixin):
    model = models.DayPlan


# ---------------------------------------------------------------------------------------
#                                                                         Necessary Plans
# ---------------------------------------------------------------------------------------
class NecessaryLists(ListMixin):
    model = models.NecessaryPlan


class NecessaryNew(CreateAjaxMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm


class NecessaryUpdate(UpdateAjaxMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm


class NecessaryDelete(DeleteAjaxMixin):
    model = models.NecessaryPlan


# ---------------------------------------------------------------------------------------
#                                                                              Copy Plans
# ---------------------------------------------------------------------------------------
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
        'title': _('Copy plans'),
        'form': form,
        'submit_button': _('Insert'),
        'form_action': 'insert',
        'url': reverse('plans:copy_plans'),
    }

    data['html_form'] = render_to_string(
        template_name='plans/includes/copy_plans_form.html',
        context=context,
        request=request
    )

    return JsonResponse(data)
