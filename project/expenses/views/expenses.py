from datetime import date, datetime
from functools import partial
from typing import Any, cast

from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ...core.lib.chart_months import ChartMonths
from ...core.lib.convert_price import PriceToFloatViewMixin
from ...core.lib.overview_cards import OverviewCards
from ...core.lib.utils import add_fast_urls, get_action_buttons_html, int_or_zero
from ...core.lib.year_boundary import YearBoundary
from ...core.mixins.tabs import TabViewMixin as CoreTabViewMixin
from ...core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    SearchViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from ...users.models import User
from .. import forms
from ..apps import App_name
from ..services import search
from ..services.cards import LARGEST_TYPE_EXPLANATION
from ..services.model_services import (
    ExpenseModelService,
    ExpenseNameModelService,
)
from ..tabs import TABS


class GetMonthMixin:
    kwargs: dict[str, Any]

    def get_month(self):
        return self.kwargs.get("month") or datetime.now().month


class TabViewMixin(CoreTabViewMixin):
    tabs = TABS
    default_tab = TABS["index"]
    app_title = _("Expenses")
    page_template = "expenses/index.html"


class TabIndex(TabViewMixin, TemplateViewMixin):
    def get_context_data(self, **kwargs):
        boundary = YearBoundary(self.request.user.selected_year(), date.today())
        service = ExpenseModelService(self.request.user)

        return {
            **super().get_context_data(**kwargs),
            "cards": OverviewCards.build(
                list(service.sum_by_between("expense_type", *boundary.span)),
                list(service.sum_by_between("expense_type", *boundary.previous_span)),
                boundary,
                LARGEST_TYPE_EXPLANATION,
            ),
            "chart": ChartMonths.build(
                list(service.sum_by_month_between(*boundary.span)),
                list(service.sum_by_month_between(*boundary.previous_span)),
                boundary,
            ),
        }


class TabData(GetMonthMixin, TabViewMixin, TemplateViewMixin):
    tab = TABS["data"]

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"month": self.get_month()}


class Lists(GetMonthMixin, ListViewMixin):
    template_name = "expenses/expense_list.html"

    def calendar_month(self) -> int:
        month = self.get_month()
        # tab 13 lists every month
        if month not in range(1, 13):
            return 0
        return month

    def get_queryset(self):
        month = self.calendar_month()
        user = cast(User, self.request.user)
        year = user.selected_year()
        service = ExpenseModelService(user)
        qs = service.year(year)
        if month:
            qs = qs.filter(date__month=month)

        data = service.expenses_list(qs)

        return add_fast_urls(data=data, app_name=App_name)

    def get_context_data(self, **kwargs):
        context = {"notice_month": self.calendar_month()}
        return super().get_context_data(**kwargs) | context | get_action_buttons_html()


class New(CreateViewMixin):
    form_class = forms.ExpenseForm
    success_url = reverse_lazy("expenses:list")
    hx_trigger_form = "reload"
    modal_form_title = _("Expenses")
    template_name = "expenses/expense_form.html"


class Update(PriceToFloatViewMixin, UpdateViewMixin):
    service_class = ExpenseModelService
    form_class = forms.ExpenseForm
    success_url = reverse_lazy("expenses:list")
    hx_trigger_django = "reload"
    modal_form_title = _("Expenses")
    template_name = "expenses/expense_form.html"


class Delete(DeleteViewMixin):
    service_class = ExpenseModelService
    success_url = reverse_lazy("expenses:list")
    modal_form_title = _("Delete expense")


class Search(SearchViewMixin):
    template_name = "expenses/expense_list.html"
    search_method = staticmethod(search.search_expenses)
    search_totals = staticmethod(search.search_totals)
    search_rows = staticmethod(partial(add_fast_urls, app_name=App_name))


class LoadExpenseName(ListViewMixin):
    template_name = "core/dropdown.html"

    def get(self, request, *args, **kwargs) -> HttpResponse:
        field = "expense_type"
        if prefix := request.GET.get("prefix", ""):
            field = f"{prefix}-expense_type"

        expense_type_pk = int_or_zero(request.GET.get(field))
        self.object_list = []
        if expense_type_pk:
            year = int_or_zero(request.GET.get("year")) or request.user.selected_year()
            self.object_list = (
                ExpenseNameModelService(request.user)
                .year(year)
                .filter(parent=expense_type_pk)
            )

        return self.render_to_response({"object_list": self.object_list})
