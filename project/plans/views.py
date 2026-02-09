from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import PlansConvertToPriceMixin
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
from .services.model_services import ModelService


class CssClassMixin:
    modal_body_css_class = "plans-form"


class Stats(TemplateViewMixin):
    template_name = "plans/stats.html"

    def get_context_data(self, **kwargs):
        data = PlanCollectData(self.request.user)
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
        user = self.request.user
        return ModelService(models.ExpensePlan, user).year(user.year)


class ExpensesNew(CssClassMixin, CreateViewMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm
    hx_trigger_django = "reloadExpenses"
    modal_form_title = _("Expenses plans")
    url_name = "expense_new"
    success_url = reverse_lazy("plans:expense_list")


class ExpensesUpdate(CssClassMixin, PlansConvertToPriceMixin, UpdateViewMixin):
    model = models.ExpensePlan
    form_class = forms.ExpensePlanForm
    hx_trigger_django = "reloadExpenses"
    modal_form_title = _("Expenses plans")
    url_name = "expense_update"
    success_url = reverse_lazy("plans:expense_list")


class ExpensesDelete(DeleteViewMixin):
    model = models.ExpensePlan
    hx_trigger_django = "reloadExpenses"
    modal_form_title = _("Delete plan")
    url_name = "expense_delete"
    success_url = reverse_lazy("plans:expense_list")


# -------------------------------------------------------------------------------------
#                                                                          Income Plans
# -------------------------------------------------------------------------------------
class IncomesLists(ListViewMixin):
    model = models.IncomePlan

    def get_queryset(self):
        user = self.request.user
        return ModelService(models.IncomePlan, user).year(user.year)


class IncomesNew(CssClassMixin, CreateViewMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm
    url_name = "income_new"
    success_url = reverse_lazy("plans:income_list")
    hx_trigger_django = "reloadIncomes"
    modal_form_title = _("Incomes plans")


class IncomesUpdate(CssClassMixin, PlansConvertToPriceMixin, UpdateViewMixin):
    model = models.IncomePlan
    form_class = forms.IncomePlanForm
    hx_trigger_django = "reloadIncomes"
    modal_form_title = _("Incomes plans")
    url_name = "income_update"
    success_url = reverse_lazy("plans:income_list")


class IncomesDelete(DeleteViewMixin):
    model = models.IncomePlan
    hx_trigger_django = "reloadIncomes"
    modal_form_title = _("Delete plan")
    url_name = "income_delete"
    success_url = reverse_lazy("plans:income_list")


# -------------------------------------------------------------------------------------
#                                                                          Saving Plans
# -------------------------------------------------------------------------------------
class SavingsLists(ListViewMixin):
    model = models.SavingPlan

    def get_queryset(self):
        user = self.request.user
        return ModelService(models.SavingPlan, user).year(user.year)


class SavingsNew(CssClassMixin, CreateViewMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm
    url_name = "saving_new"
    success_url = reverse_lazy("plans:saving_list")
    hx_trigger_django = "reloadSavings"
    modal_form_title = _("Savings plans")


class SavingsUpdate(CssClassMixin, PlansConvertToPriceMixin, UpdateViewMixin):
    model = models.SavingPlan
    form_class = forms.SavingPlanForm
    hx_trigger_django = "reloadSavings"
    modal_form_title = _("Savings plans")
    url_name = "saving_update"
    success_url = reverse_lazy("plans:saving_list")


class SavingsDelete(DeleteViewMixin):
    model = models.SavingPlan
    hx_trigger_django = "reloadSavings"
    modal_form_title = _("Delete plan")
    url_name = "saving_delete"
    success_url = reverse_lazy("plans:saving_list")


# -------------------------------------------------------------------------------------
#                                                                             Day Plans
# -------------------------------------------------------------------------------------
class DayLists(ListViewMixin):
    model = models.DayPlan

    def get_queryset(self):
        user = self.request.user
        return ModelService(models.DayPlan, user).year(user.year)


class DayNew(CssClassMixin, CreateViewMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm
    url_name = "day_new"
    success_url = reverse_lazy("plans:day_list")
    hx_trigger_django = "reloadDay"
    modal_form_title = _("Day plans")


class DayUpdate(CssClassMixin, PlansConvertToPriceMixin, UpdateViewMixin):
    model = models.DayPlan
    form_class = forms.DayPlanForm
    hx_trigger_django = "reloadDay"
    modal_form_title = _("Day plans")
    url_name = "day_update"
    success_url = reverse_lazy("plans:day_list")


class DayDelete(DeleteViewMixin):
    model = models.DayPlan
    hx_trigger_django = "reloadDay"
    modal_form_title = _("Delete plan")
    url_name = "day_delete"
    success_url = reverse_lazy("plans:day_list")


# -------------------------------------------------------------------------------------
#                                                                       Necessary Plans
# -------------------------------------------------------------------------------------
class NecessaryLists(ListViewMixin):
    model = models.NecessaryPlan

    def get_queryset(self):
        user = self.request.user
        return ModelService(models.NecessaryPlan, user).year(user.year)


class NecessaryNew(CssClassMixin, CreateViewMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm
    url_name = "necessary_new"
    hx_trigger_django = "reloadNecessary"
    modal_form_title = _("Additional necessary expenses")
    success_url = reverse_lazy("plans:necessary_list")


class NecessaryUpdate(CssClassMixin, PlansConvertToPriceMixin, UpdateViewMixin):
    model = models.NecessaryPlan
    form_class = forms.NecessaryPlanForm
    hx_trigger_django = "reloadNecessary"
    modal_form_title = _("Additional necessary expenses")
    url_name = "necessary_update"
    success_url = reverse_lazy("plans:necessary_list")


class NecessaryDelete(DeleteViewMixin):
    model = models.NecessaryPlan
    hx_trigger_django = "reloadNecessary"
    modal_form_title = _("Delete plan")
    url_name = "necessary_delete"
    success_url = reverse_lazy("plans:necessary_list")


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
