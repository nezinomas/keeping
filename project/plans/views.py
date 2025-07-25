from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import PlansConvertToCents
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    FormViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
    http_htmx_response,
    rendered_content,
)
from . import forms, models
from .lib.calc_day_sum import PlanCalculateDaySum, PlanCollectData


class CssClassMixin:
    modal_body_css_class = "plans-form"


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


class ExpensesNew(CssClassMixin, CreateViewMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm
    url = reverse_lazy("plans:expense_new")
    success_url = reverse_lazy("plans:expense_list")
    hx_trigger_django = "reloadExpenses"
    modal_form_title = _("Expenses plans")


class ExpensesUpdate(CssClassMixin, PlansConvertToCents, UpdateViewMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm
    success_url = reverse_lazy("plans:expense_list")
    hx_trigger_django = "reloadExpenses"
    modal_form_title = _("Expenses plans")


class ExpensesDelete(DeleteViewMixin):
    model = models.ExpensePlan
    success_url = reverse_lazy("plans:expense_list")
    hx_trigger_django = "reloadExpenses"
    modal_form_title = _("Delete plan")


# -------------------------------------------------------------------------------------
#                                                                          Income Plans
# -------------------------------------------------------------------------------------
class IncomesLists(ListViewMixin):
    model = models.IncomePlan

    def get_queryset(self):
        return models.IncomePlan.objects.year(year=self.request.user.year)


class IncomesNew(CssClassMixin, CreateViewMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm
    url = reverse_lazy("plans:income_new")
    success_url = reverse_lazy("plans:income_list")
    hx_trigger_django = "reloadIncomes"
    modal_form_title = _("Incomes plans")


class IncomesUpdate(CssClassMixin, PlansConvertToCents, UpdateViewMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm
    success_url = reverse_lazy("plans:income_list")
    hx_trigger_django = "reloadIncomes"
    modal_form_title = _("Incomes plans")


class IncomesDelete(DeleteViewMixin):
    model = models.IncomePlan
    success_url = reverse_lazy("plans:income_list")
    hx_trigger_django = "reloadIncomes"
    modal_form_title = _("Delete plan")


# -------------------------------------------------------------------------------------
#                                                                          Saving Plans
# -------------------------------------------------------------------------------------
class SavingsLists(ListViewMixin):
    model = models.SavingPlan

    def get_queryset(self):
        return models.SavingPlan.objects.year(year=self.request.user.year)


class SavingsNew(CssClassMixin, CreateViewMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm
    url = reverse_lazy("plans:saving_new")
    success_url = reverse_lazy("plans:saving_list")
    hx_trigger_django = "reloadSavings"
    modal_form_title = _("Savings plans")


class SavingsUpdate(CssClassMixin, PlansConvertToCents, UpdateViewMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm
    success_url = reverse_lazy("plans:saving_list")
    hx_trigger_django = "reloadSavings"
    modal_form_title = _("Savings plans")


class SavingsDelete(DeleteViewMixin):
    model = models.SavingPlan
    success_url = reverse_lazy("plans:saving_list")
    hx_trigger_django = "reloadSavings"
    modal_form_title = _("Delete plan")


# -------------------------------------------------------------------------------------
#                                                                             Day Plans
# -------------------------------------------------------------------------------------
class DayLists(ListViewMixin):
    model = models.DayPlan

    def get_queryset(self):
        return models.DayPlan.objects.year(year=self.request.user.year)


class DayNew(CssClassMixin, CreateViewMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm
    url = reverse_lazy("plans:day_new")
    success_url = reverse_lazy("plans:day_list")
    hx_trigger_django = "reloadDay"
    modal_form_title = _("Day plans")


class DayUpdate(CssClassMixin, PlansConvertToCents, UpdateViewMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm
    success_url = reverse_lazy("plans:day_list")
    hx_trigger_django = "reloadDay"
    modal_form_title = _("Day plans")


class DayDelete(DeleteViewMixin):
    model = models.DayPlan
    success_url = reverse_lazy("plans:day_list")
    hx_trigger_django = "reloadDay"
    modal_form_title = _("Delete plan")


# -------------------------------------------------------------------------------------
#                                                                       Necessary Plans
# -------------------------------------------------------------------------------------
class NecessaryLists(ListViewMixin):
    model = models.NecessaryPlan

    def get_queryset(self):
        return models.NecessaryPlan.objects.year(year=self.request.user.year)


class NecessaryNew(CssClassMixin, CreateViewMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm
    url = reverse_lazy("plans:necessary_new")
    success_url = reverse_lazy("plans:necessary_list")
    hx_trigger_django = "reloadNecessary"
    modal_form_title = _("Additional necessary expenses")


class NecessaryUpdate(CssClassMixin, PlansConvertToCents, UpdateViewMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm
    success_url = reverse_lazy("plans:necessary_list")
    hx_trigger_django = "reloadNecessary"
    modal_form_title = _("Additional necessary expenses")


class NecessaryDelete(DeleteViewMixin):
    model = models.NecessaryPlan
    success_url = reverse_lazy("plans:necessary_list")
    hx_trigger_django = "reloadNecessary"
    modal_form_title = _("Delete plan")


# -------------------------------------------------------------------------------------
#                                                                            Copy Plans
# -------------------------------------------------------------------------------------
class CopyPlans(FormViewMixin):
    form_class = forms.CopyPlanForm
    success_url = reverse_lazy("plans:index")
    hx_trigger_django = "afterCopy"
    modal_form_title = _("Copy plans")

    def get_context_data(self, **kwargs):
        context = {
            "url": reverse_lazy("plans:copy"),
            "form_action": "insert_close",
        }

        return super().get_context_data(**kwargs) | context

    def form_valid(self, form, **kwargs):
        form.save()

        return http_htmx_response(self.hx_trigger_django)
