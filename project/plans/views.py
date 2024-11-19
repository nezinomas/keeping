from django.urls import reverse_lazy

from ..core.lib.convert_price import PlansConvertToCents
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    FormViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
    httpHtmxResponse,
    rendered_content,
)
from . import forms, models
from .lib.calc_day_sum import PlanCalculateDaySum, PlanCollectData


class Stats(TemplateViewMixin):
    template_name = "plans/stats.html"

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        data = PlanCollectData(year)
        obj = PlanCalculateDaySum(data)
        context = {
            "items": obj.plans_stats,
        }

        return super().get_context_data(**kwargs) | context


class Index(TemplateViewMixin):
    template_name = "plans/index.html"

    def get_context_data(self, **kwargs):
        context = {
            "incomes_list": rendered_content(self.request, IncomesLists, **kwargs),
            "expenses_list": rendered_content(self.request, ExpensesLists, **kwargs),
            "savings_list": rendered_content(self.request, SavingsLists, **kwargs),
            "day_list": rendered_content(self.request, DayLists, **kwargs),
            "necessary_list": rendered_content(self.request, NecessaryLists, **kwargs),
            "plans_stats": rendered_content(self.request, Stats, **kwargs),
        }

        return super().get_context_data(**kwargs) | context


# -------------------------------------------------------------------------------------
#                                                                         Expense Plans
# -------------------------------------------------------------------------------------
class ExpensesLists(ListViewMixin):
    model = models.ExpensePlan

    def get_queryset(self):
        return models.ExpensePlan.objects.year(year=self.request.user.year)


class ExpensesNew(CreateViewMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm
    url = reverse_lazy("plans:expense_new")
    success_url = reverse_lazy("plans:expense_list")
    hx_trigger_django = "reloadExpenses"


class ExpensesUpdate(PlansConvertToCents, UpdateViewMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm
    success_url = reverse_lazy("plans:expense_list")
    hx_trigger_django = "reloadExpenses"


class ExpensesDelete(DeleteViewMixin):
    model = models.ExpensePlan
    success_url = reverse_lazy("plans:expense_list")
    hx_trigger_django = "reloadExpenses"


# -------------------------------------------------------------------------------------
#                                                                          Income Plans
# -------------------------------------------------------------------------------------
class IncomesLists(ListViewMixin):
    model = models.IncomePlan

    def get_queryset(self):
        return models.IncomePlan.objects.year(year=self.request.user.year)


class IncomesNew(CreateViewMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm
    url = reverse_lazy("plans:income_new")
    success_url = reverse_lazy("plans:income_list")
    hx_trigger_django = "reloadIncomes"


class IncomesUpdate(PlansConvertToCents, UpdateViewMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm
    success_url = reverse_lazy("plans:income_list")
    hx_trigger_django = "reloadIncomes"


class IncomesDelete(DeleteViewMixin):
    model = models.IncomePlan
    success_url = reverse_lazy("plans:income_list")
    hx_trigger_django = "reloadIncomes"


# -------------------------------------------------------------------------------------
#                                                                          Saving Plans
# -------------------------------------------------------------------------------------
class SavingsLists(ListViewMixin):
    model = models.SavingPlan

    def get_queryset(self):
        return models.SavingPlan.objects.year(year=self.request.user.year)


class SavingsNew(CreateViewMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm
    url = reverse_lazy("plans:saving_new")
    success_url = reverse_lazy("plans:saving_list")
    hx_trigger_django = "reloadSavings"


class SavingsUpdate(PlansConvertToCents, UpdateViewMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm
    success_url = reverse_lazy("plans:saving_list")
    hx_trigger_django = "reloadSavings"


class SavingsDelete(DeleteViewMixin):
    model = models.SavingPlan
    success_url = reverse_lazy("plans:saving_list")
    hx_trigger_django = "reloadSavings"


# -------------------------------------------------------------------------------------
#                                                                             Day Plans
# -------------------------------------------------------------------------------------
class DayLists(ListViewMixin):
    model = models.DayPlan

    def get_queryset(self):
        return models.DayPlan.objects.year(year=self.request.user.year)


class DayNew(CreateViewMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm
    url = reverse_lazy("plans:day_new")
    success_url = reverse_lazy("plans:day_list")
    hx_trigger_django = "reloadDay"


class DayUpdate(PlansConvertToCents, UpdateViewMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm
    success_url = reverse_lazy("plans:day_list")
    hx_trigger_django = "reloadDay"


class DayDelete(DeleteViewMixin):
    model = models.DayPlan
    success_url = reverse_lazy("plans:day_list")
    hx_trigger_django = "reloadDay"


# -------------------------------------------------------------------------------------
#                                                                       Necessary Plans
# -------------------------------------------------------------------------------------
class NecessaryLists(ListViewMixin):
    model = models.NecessaryPlan

    def get_queryset(self):
        return models.NecessaryPlan.objects.year(year=self.request.user.year)


class NecessaryNew(CreateViewMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm
    url = reverse_lazy("plans:necessary_new")
    success_url = reverse_lazy("plans:necessary_list")
    hx_trigger_django = "reloadNecessary"


class NecessaryUpdate(PlansConvertToCents, UpdateViewMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm
    success_url = reverse_lazy("plans:necessary_list")
    hx_trigger_django = "reloadNecessary"


class NecessaryDelete(DeleteViewMixin):
    model = models.NecessaryPlan
    success_url = reverse_lazy("plans:necessary_list")
    hx_trigger_django = "reloadNecessary"


# -------------------------------------------------------------------------------------
#                                                                            Copy Plans
# -------------------------------------------------------------------------------------
class CopyPlans(FormViewMixin):
    form_class = forms.CopyPlanForm
    template_name = "plans/copyplan_form.html"
    success_url = reverse_lazy("plans:index")
    hx_trigger_django = "afterCopy"

    def get_context_data(self, **kwargs):
        context = {
            "url": reverse_lazy("plans:copy"),
            "form_action": "insert_close",
        }

        return super().get_context_data(**kwargs) | context

    def form_valid(self, form, **kwargs):
        form.save()

        return httpHtmxResponse(self.hx_trigger_django)
