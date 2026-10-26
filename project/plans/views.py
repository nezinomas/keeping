from datetime import date

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.utils import http_htmx_response
from ..core.mixins.tabs import TabViewMixin as CoreTabViewMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    FormViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from . import forms
from .lib.calc_day_sum import DataDto, PlanCalculateDaySum, PlanCollectData
from .mixins.views import PlanDeleteMixin, PlanFormMixin, PlanObjectMixin
from .services.calculations import Calculations
from .services.cards import DayCards, ExpenseCards, IncomeCards, SavingCards
from .services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    NecessaryPlanModelService,
    SavingPlanModelService,
)
from .tabs import TABS


class TabViewMixin(CoreTabViewMixin):
    tabs = TABS
    # the outcome the other three tabs feed, so it opens first
    default_tab = TABS["day"]
    app_title = _("Plans")
    page_template = "plans/index.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "plan_year": self.request.user.selected_year(),
        }

    def plan_data(self) -> DataDto:
        user = self.request.user
        return PlanCollectData(user, user.selected_year()).get_data()


class TabIncomes(TabViewMixin, TemplateViewMixin):
    tab = TABS["incomes"]

    def get_context_data(self, **kwargs):
        user = self.request.user
        year = user.selected_year()
        return {
            **super().get_context_data(**kwargs),
            "income_plans": IncomePlanModelService(user).rows(year),
            "cards": IncomeCards.build(self.plan_data()),
        }


class IncomesNew(PlanFormMixin, CreateViewMixin):
    form_class = forms.IncomePlanForm
    url_name = "income_new"
    success_url = reverse_lazy("plans:tab_incomes")
    hx_trigger_django = "reload"
    modal_form_title = _("Incomes plans")


class IncomesUpdate(PlanFormMixin, PlanObjectMixin, UpdateViewMixin):
    service_class = IncomePlanModelService
    form_class = forms.IncomePlanForm
    hx_trigger_django = "reload"
    modal_form_title = _("Incomes plans")
    url_name = "income_update"
    success_url = reverse_lazy("plans:tab_incomes")


class IncomesDelete(PlanDeleteMixin, DeleteViewMixin):
    service_class = IncomePlanModelService
    hx_trigger_django = "reload"
    modal_form_title = _("Delete plan")
    url_name = "income_delete"
    success_url = reverse_lazy("plans:tab_incomes")


class TabExpenses(TabViewMixin, TemplateViewMixin):
    tab = TABS["expenses"]

    def get_context_data(self, **kwargs):
        user = self.request.user
        year = user.selected_year()
        return {
            **super().get_context_data(**kwargs),
            "expense_plans": ExpensePlanModelService(user).row_tables(year),
            "necessary_plans": NecessaryPlanModelService(user).rows(year),
            "cards": ExpenseCards.build(self.plan_data()),
        }


class ExpensesNew(PlanFormMixin, CreateViewMixin):
    form_class = forms.ExpensePlanForm
    hx_trigger_django = "reload"
    modal_form_title = _("Expenses plans")
    url_name = "expense_new"
    success_url = reverse_lazy("plans:tab_expenses")


class ExpensesUpdate(PlanFormMixin, PlanObjectMixin, UpdateViewMixin):
    service_class = ExpensePlanModelService
    form_class = forms.ExpensePlanForm
    hx_trigger_django = "reload"
    modal_form_title = _("Expenses plans")
    url_name = "expense_update"
    success_url = reverse_lazy("plans:tab_expenses")


class ExpensesDelete(PlanDeleteMixin, DeleteViewMixin):
    service_class = ExpensePlanModelService
    hx_trigger_django = "reload"
    modal_form_title = _("Delete plan")
    url_name = "expense_delete"
    success_url = reverse_lazy("plans:tab_expenses")


class TabSavings(TabViewMixin, TemplateViewMixin):
    tab = TABS["savings"]

    def get_context_data(self, **kwargs):
        user = self.request.user
        year = user.selected_year()
        return {
            **super().get_context_data(**kwargs),
            "saving_plans": SavingPlanModelService(user).rows(year),
            "cards": SavingCards.build(self.plan_data()),
        }


class SavingsNew(PlanFormMixin, CreateViewMixin):
    form_class = forms.SavingPlanForm
    url_name = "saving_new"
    success_url = reverse_lazy("plans:tab_savings")
    hx_trigger_django = "reload"
    modal_form_title = _("Savings plans")


class SavingsUpdate(PlanFormMixin, PlanObjectMixin, UpdateViewMixin):
    service_class = SavingPlanModelService
    form_class = forms.SavingPlanForm
    hx_trigger_django = "reload"
    modal_form_title = _("Savings plans")
    url_name = "saving_update"
    success_url = reverse_lazy("plans:tab_savings")


class SavingsDelete(PlanDeleteMixin, DeleteViewMixin):
    service_class = SavingPlanModelService
    hx_trigger_django = "reload"
    modal_form_title = _("Delete plan")
    url_name = "saving_delete"
    success_url = reverse_lazy("plans:tab_savings")


class TabDay(TabViewMixin, TemplateViewMixin):
    def get_context_data(self, **kwargs):
        user = self.request.user
        year = user.selected_year()
        data = self.plan_data()
        calc = PlanCalculateDaySum(data)
        # this month = today's month number, in whichever Plan year is selected
        month = date.today().month

        return {
            **super().get_context_data(**kwargs),
            "day_plans": DayPlanModelService(user).rows(year, calc.day_plan_states()),
            "calculations": Calculations.build(calc),
            "cards": DayCards.build(calc, month),
        }


class DayNew(PlanFormMixin, CreateViewMixin):
    form_class = forms.DayPlanForm
    url_name = "day_new"
    success_url = reverse_lazy("plans:tab_day")
    hx_trigger_django = "reload"
    modal_form_title = _("Day plans")


class DayUpdate(PlanFormMixin, PlanObjectMixin, UpdateViewMixin):
    service_class = DayPlanModelService
    form_class = forms.DayPlanForm
    hx_trigger_django = "reload"
    modal_form_title = _("Day plans")
    url_name = "day_update"
    success_url = reverse_lazy("plans:tab_day")


class DayDelete(PlanDeleteMixin, DeleteViewMixin):
    service_class = DayPlanModelService
    hx_trigger_django = "reload"
    modal_form_title = _("Delete plan")
    url_name = "day_delete"
    success_url = reverse_lazy("plans:tab_day")


class NecessaryNew(PlanFormMixin, CreateViewMixin):
    form_class = forms.NecessaryPlanForm
    url_name = "necessary_new"
    hx_trigger_django = "reload"
    modal_form_title = _("Additional necessary expenses")
    success_url = reverse_lazy("plans:tab_expenses")


class NecessaryUpdate(PlanFormMixin, PlanObjectMixin, UpdateViewMixin):
    service_class = NecessaryPlanModelService
    form_class = forms.NecessaryPlanForm
    hx_trigger_django = "reload"
    modal_form_title = _("Additional necessary expenses")
    url_name = "necessary_update"
    success_url = reverse_lazy("plans:tab_expenses")


class NecessaryDelete(PlanDeleteMixin, DeleteViewMixin):
    service_class = NecessaryPlanModelService
    hx_trigger_django = "reload"
    modal_form_title = _("Delete plan")
    url_name = "necessary_delete"
    success_url = reverse_lazy("plans:tab_expenses")


class CopyPlans(FormViewMixin):
    form_class = forms.CopyPlanForm
    success_url = reverse_lazy("plans:index")
    hx_trigger_django = "reload"
    modal_form_title = _("Copy plans")

    def get_context_data(self, **kwargs):
        context = {
            "url": reverse_lazy("plans:copy"),
            "form_action": "insert_close",
        }

        return super().get_context_data(**kwargs) | context

    def form_valid(self, form):
        form.save()

        return http_htmx_response(self.hx_trigger_django)
