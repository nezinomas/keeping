from django.http import Http404, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import PlansConvertPriceMixin
from ..core.lib.utils import http_htmx_response, rendered_content
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    FormViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from . import forms
from .lib.calc_day_sum import PlanCalculateDaySum, PlanCollectData
from .services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    NecessaryPlanModelService,
    SavingPlanModelService,
)


class CssClassMixin:
    modal_body_css_class = "plans-form"


class TallRecordMixin:
    def get_tall_queryset(self):
        # 1. Get the base queryset for this user and service
        qs = self.service_class(self.request.user).items()

        # 2. Filter using exactly the kwargs provided in the URL!
        # If the URL is incomes/1999/5/, self.kwargs is {'year': 1999, 'income_type_id': 5}
        # qs.filter(**self.kwargs) translates instantly to qs.filter(year=1999, income_type_id=5)
        q = qs.filter(**self.kwargs)
        print(f'--------------------------->{q=}\n')
        return q

class TallUpdateMixin(TallRecordMixin):
    """DRY Mixin for UpdateViews using Tall tables."""
    def get_object(self, queryset=None):
        # We just need ONE row to act as the "Instance" for the Proxy Form to read
        obj = self.get_tall_queryset().first()
        if not obj:
            raise Http404(_("No plans found."))
        return obj

    def url(self):
        if not self.object:
            return None

        return reverse_lazy(f"plans:{self.url_name}", kwargs=self.kwargs)

class TallDeleteMixin(TallRecordMixin):
    def get_object(self, queryset=None):
        if obj := self.get_tall_queryset().first():
            return obj

        raise Http404(_("No plans found."))

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self.get_tall_queryset().delete()
        return response

    def url(self):
        if not self.object:
            return None

        # Same ultra-simple logic here
        return reverse_lazy(f"plans:{self.url_name}", kwargs=self.kwargs)


class Stats(TemplateViewMixin):
    template_name = "plans/stats.html"

    def get_context_data(self, **kwargs):
        user = self.request.user

        data = PlanCollectData(user, user.year).get_data()
        obj = PlanCalculateDaySum(data)
        context = {
            "object_list": obj.plans_stats(),
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
    template_name = "plans/expenseplan_list.html"
    service_class = ExpensePlanModelService
    plan_type = "expense"

    def get_queryset(self):
        user = self.request.user
        return ExpensePlanModelService(user).pivot_table(user.year)


class ExpensesNew(CssClassMixin, CreateViewMixin):
    service_class = ExpensePlanModelService
    form_class = forms.ExpensePlanForm
    hx_trigger_django = "reloadExpenses"
    modal_form_title = _("Expenses plans")
    url_name = "expense_new"
    success_url = reverse_lazy("plans:expense_list")


class ExpensesUpdate(CssClassMixin, PlansConvertPriceMixin, UpdateViewMixin):
    service_class = ExpensePlanModelService
    form_class = forms.ExpensePlanForm
    hx_trigger_django = "reloadExpenses"
    modal_form_title = _("Expenses plans")
    url_name = "expense_update"
    success_url = reverse_lazy("plans:expense_list")


class ExpensesDelete(DeleteViewMixin):
    service_class = ExpensePlanModelService
    hx_trigger_django = "reloadExpenses"
    modal_form_title = _("Delete plan")
    url_name = "expense_delete"
    success_url = reverse_lazy("plans:expense_list")


# -------------------------------------------------------------------------------------
#                                                                          Income Plans
# -------------------------------------------------------------------------------------
class IncomesLists(ListViewMixin):
    template_name = "plans/incomeplan_list.html"
    service_class = IncomePlanModelService
    plan_type = "income"

    def get_queryset(self):
        user = self.request.user
        return IncomePlanModelService(user).pivot_table(user.year)


class IncomesNew(CssClassMixin, CreateViewMixin):
    service_class = IncomePlanModelService
    form_class = forms.IncomePlanForm
    url_name = "income_new"
    success_url = reverse_lazy("plans:income_list")
    hx_trigger_django = "reloadIncomes"
    modal_form_title = _("Incomes plans")


class IncomesUpdate(CssClassMixin, PlansConvertPriceMixin, TallUpdateMixin, UpdateViewMixin):
    service_class = IncomePlanModelService
    # lookup_field = "category_pk"
    form_class = forms.IncomePlanForm
    hx_trigger_django = "reloadIncomes"
    modal_form_title = _("Incomes plans")
    url_name = "income_update"
    success_url = reverse_lazy("plans:income_list")


class IncomesDelete(TallDeleteMixin, DeleteViewMixin):
    service_class = IncomePlanModelService
    hx_trigger_django = "reloadIncomes"
    modal_form_title = _("Delete plan")
    url_name = "income_delete"
    success_url = reverse_lazy("plans:income_list")


# -------------------------------------------------------------------------------------
#                                                                          Saving Plans
# -------------------------------------------------------------------------------------
class SavingsLists(ListViewMixin):
    template_name = "plans/savingplan_list.html"
    service_class = SavingPlanModelService
    plan_type = "saving"

    def get_queryset(self):
        user = self.request.user
        return SavingPlanModelService(user).pivot_table(user.year)


class SavingsNew(CssClassMixin, CreateViewMixin):
    service_class = SavingPlanModelService
    form_class = forms.SavingPlanForm
    url_name = "saving_new"
    success_url = reverse_lazy("plans:saving_list")
    hx_trigger_django = "reloadSavings"
    modal_form_title = _("Savings plans")


class SavingsUpdate(CssClassMixin, PlansConvertPriceMixin, UpdateViewMixin):
    service_class = SavingPlanModelService
    form_class = forms.SavingPlanForm
    hx_trigger_django = "reloadSavings"
    modal_form_title = _("Savings plans")
    url_name = "saving_update"
    success_url = reverse_lazy("plans:saving_list")


class SavingsDelete(DeleteViewMixin):
    service_class = SavingPlanModelService
    hx_trigger_django = "reloadSavings"
    modal_form_title = _("Delete plan")
    url_name = "saving_delete"
    success_url = reverse_lazy("plans:saving_list")


# -------------------------------------------------------------------------------------
#                                                                             Day Plans
# -------------------------------------------------------------------------------------
class DayLists(ListViewMixin):
    template_name = "plans/dayplan_list.html"
    service_class = DayPlanModelService
    plan_type = "day"

    def get_queryset(self):
        user = self.request.user
        return DayPlanModelService(user).pivot_table(user.year)


class DayNew(CssClassMixin, CreateViewMixin):
    service_class = DayPlanModelService
    form_class = forms.DayPlanForm
    url_name = "day_new"
    success_url = reverse_lazy("plans:day_list")
    hx_trigger_django = "reloadDay"
    modal_form_title = _("Day plans")


class DayUpdate(CssClassMixin, PlansConvertPriceMixin, UpdateViewMixin):
    service_class = DayPlanModelService
    form_class = forms.DayPlanForm
    hx_trigger_django = "reloadDay"
    modal_form_title = _("Day plans")
    url_name = "day_update"
    success_url = reverse_lazy("plans:day_list")


class DayDelete(DeleteViewMixin):
    service_class = DayPlanModelService
    hx_trigger_django = "reloadDay"
    modal_form_title = _("Delete plan")
    url_name = "day_delete"
    success_url = reverse_lazy("plans:day_list")


# -------------------------------------------------------------------------------------
#                                                                       Necessary Plans
# -------------------------------------------------------------------------------------
class NecessaryLists(ListViewMixin):
    template_name = "plans/necessaryplan_list.html"
    service_class = NecessaryPlanModelService
    plan_type = "necessary"

    def get_queryset(self):
        user = self.request.user
        return NecessaryPlanModelService(user).pivot_table(user.year)


class NecessaryNew(CssClassMixin, CreateViewMixin):
    service_class = NecessaryPlanModelService
    form_class = forms.NecessaryPlanForm
    url_name = "necessary_new"
    hx_trigger_django = "reloadNecessary"
    modal_form_title = _("Additional necessary expenses")
    success_url = reverse_lazy("plans:necessary_list")


class NecessaryUpdate(CssClassMixin, PlansConvertPriceMixin, UpdateViewMixin):
    service_class = NecessaryPlanModelService
    form_class = forms.NecessaryPlanForm
    hx_trigger_django = "reloadNecessary"
    modal_form_title = _("Additional necessary expenses")
    url_name = "necessary_update"
    success_url = reverse_lazy("plans:necessary_list")


class NecessaryDelete(DeleteViewMixin):
    service_class = NecessaryPlanModelService
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
