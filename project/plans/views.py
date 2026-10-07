from datetime import date

from django.urls import reverse_lazy
from django.utils.text import format_lazy
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
from .mixins.views import CssClassMixin, PlanDeleteMixin, PlanUpdateMixin
from .services.calculations import Calculations
from .services.cards import DayCards, ExpenseCards, IncomeCards, SavingCards
from .services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    NecessaryPlanModelService,
    SavingPlanModelService,
)
from .tabs import DEFAULT_TAB, TABS, PlanTab


class TabViewMixin(CoreTabViewMixin):
    tab = DEFAULT_TAB
    fragment_template = "plans/tab_fragment.html"
    page_template = "plans/index.html"

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "tab_url": self.tab.url}

    def page_context(self) -> dict:
        return {
            "page_title": format_lazy("{} | {}", _("Plans"), self.tab.title),
            "tabs": [(tab, tab.url) for tab in TABS],
        }

    def plan_data(self) -> DataDto:
        user = self.request.user
        return PlanCollectData(user, user.year).get_data()


class TabIncomes(TabViewMixin, TemplateViewMixin):
    tab = PlanTab.resolve("incomes")

    def get_context_data(self, **kwargs):
        user = self.request.user
        return {
            **super().get_context_data(**kwargs),
            "income_plans": IncomePlanModelService(user).pivot_table(user.year),
            "cards": IncomeCards.build(self.plan_data()),
        }


class IncomesNew(CssClassMixin, CreateViewMixin):
    service_class = IncomePlanModelService
    form_class = forms.IncomePlanForm
    url_name = "income_new"
    success_url = reverse_lazy("plans:tab_incomes")
    hx_trigger_django = "reload"
    modal_form_title = _("Incomes plans")


class IncomesUpdate(CssClassMixin, PlanUpdateMixin, UpdateViewMixin):
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
    tab = PlanTab.resolve("expenses")

    def get_context_data(self, **kwargs):
        user = self.request.user
        return {
            **super().get_context_data(**kwargs),
            "expense_plans": ExpensePlanModelService(user).pivot_tables(user.year),
            "necessary_plans": NecessaryPlanModelService(user).pivot_table(user.year),
            "cards": ExpenseCards.build(self.plan_data()),
        }


class ExpensesNew(CssClassMixin, CreateViewMixin):
    service_class = ExpensePlanModelService
    form_class = forms.ExpensePlanForm
    hx_trigger_django = "reload"
    modal_form_title = _("Expenses plans")
    url_name = "expense_new"
    success_url = reverse_lazy("plans:tab_expenses")


class ExpensesUpdate(CssClassMixin, PlanUpdateMixin, UpdateViewMixin):
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
    tab = PlanTab.resolve("savings")

    def get_context_data(self, **kwargs):
        user = self.request.user
        return {
            **super().get_context_data(**kwargs),
            "saving_plans": SavingPlanModelService(user).pivot_table(user.year),
            "cards": SavingCards.build(self.plan_data()),
        }


class SavingsNew(CssClassMixin, CreateViewMixin):
    service_class = SavingPlanModelService
    form_class = forms.SavingPlanForm
    url_name = "saving_new"
    success_url = reverse_lazy("plans:tab_savings")
    hx_trigger_django = "reload"
    modal_form_title = _("Savings plans")


class SavingsUpdate(CssClassMixin, PlanUpdateMixin, UpdateViewMixin):
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
    tab = PlanTab.resolve("day")

    def get_context_data(self, **kwargs):
        user = self.request.user
        data = self.plan_data()
        calc = PlanCalculateDaySum(data)
        # this month = today's month number, in whichever Plan year is selected
        month = date.today().month

        return {
            **super().get_context_data(**kwargs),
            "day_plans": DayPlanModelService(user).pivot_table(user.year),
            "calculations": Calculations.build(calc),
            "cards": DayCards.build(data, month),
            "day_states": calc.day_plan_states(),
        }


class DayNew(CssClassMixin, CreateViewMixin):
    service_class = DayPlanModelService
    form_class = forms.DayPlanForm
    url_name = "day_new"
    success_url = reverse_lazy("plans:tab_day")
    hx_trigger_django = "reload"
    modal_form_title = _("Day plans")


class DayUpdate(CssClassMixin, PlanUpdateMixin, UpdateViewMixin):
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


class NecessaryNew(CssClassMixin, CreateViewMixin):
    service_class = NecessaryPlanModelService
    form_class = forms.NecessaryPlanForm
    url_name = "necessary_new"
    hx_trigger_django = "reload"
    modal_form_title = _("Additional necessary expenses")
    success_url = reverse_lazy("plans:tab_expenses")


class NecessaryUpdate(CssClassMixin, PlanUpdateMixin, UpdateViewMixin):
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

    def form_valid(self, form, **kwargs):
        form.save()

        return http_htmx_response(self.hx_trigger_django)
