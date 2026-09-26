from datetime import date

from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import ConvertPriceMixin
from ..core.lib.year_boundary import YearBoundary
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    SearchViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from . import forms
from .services.cards import OverviewCards
from .services.chart_months import ChartMonths
from .services.model_services import IncomeModelService, IncomeTypeModelService
from .tabs import DEFAULT_TAB, TABS, IncomeTab


class TabViewMixin:
    tab = DEFAULT_TAB

    def get_template_names(self):
        return [self.tab.template_name]

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "tab": self.tab.name}

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        page = {**context, **self._page(), "content": response.rendered_content}

        if self.request.htmx:
            return render(self.request, "incomes/tab_fragment.html", page)

        return render(self.request, "incomes/index.html", page)

    def _page(self) -> dict:
        return {
            "tab_url": self.tab.url,
            "page_title": format_lazy("{} | {}", _("Incomes"), self.tab.title),
            "tabs": [(tab, tab.url) for tab in TABS],
        }


class TabIndex(TabViewMixin, TemplateViewMixin):
    tab = IncomeTab.resolve("index")

    def get_context_data(self, **kwargs):
        boundary = YearBoundary.for_year(self.request.user.year)
        service = IncomeModelService(self.request.user)
        this_span = (date(boundary.year, 1, 1), boundary.end_date)
        last_span = (date(boundary.year - 1, 1, 1), boundary.previous_end_date)

        return {
            **super().get_context_data(**kwargs),
            "cards": OverviewCards.build(
                list(service.sum_by_type_between(*this_span)),
                list(service.sum_by_type_between(*last_span)),
                boundary,
            ),
            "chart": ChartMonths.build(
                list(service.sum_by_month_between(*this_span)),
                list(service.sum_by_month_between(*last_span)),
                boundary,
            ),
        }


class Lists(ListViewMixin):
    template_name = "incomes/income_list.html"
    service_class = IncomeModelService

    def get_queryset(self):
        user = self.request.user
        return (
            IncomeModelService(user)
            .year(user.year)
            .order_by("-date", "price")
            .values(
                "id", "date", "income_type__title", "account__title", "price", "remark"
            )
        )


class TabData(TabViewMixin, Lists):
    tab = IncomeTab.resolve("data")


class TabTypes(TabViewMixin, ListViewMixin):
    tab = IncomeTab.resolve("types")
    service_class = IncomeTypeModelService


# the nav and Bookkeeping open these too, so they take no tab kwarg
class New(CreateViewMixin):
    service_class = IncomeModelService
    form_class = forms.IncomeForm
    success_url = reverse_lazy("incomes:tab_data")
    hx_trigger_form = "reload"
    modal_form_title = _("Incomes")


class Update(ConvertPriceMixin, UpdateViewMixin):
    service_class = IncomeModelService
    form_class = forms.IncomeForm
    success_url = reverse_lazy("incomes:tab_data")
    hx_trigger_django = "reload"
    modal_form_title = _("Incomes")


class Delete(DeleteViewMixin):
    service_class = IncomeModelService
    success_url = reverse_lazy("incomes:tab_data")
    modal_form_title = _("Delete income")


class TypeNew(CreateViewMixin):
    service_class = IncomeTypeModelService
    form_class = forms.IncomeTypeForm
    hx_trigger_django = "reload"
    modal_form_title = _("Incomes type")
    url_name = "type_new"
    success_url = reverse_lazy("incomes:tab_types")


class TypeUpdate(UpdateViewMixin):
    service_class = IncomeTypeModelService
    form_class = forms.IncomeTypeForm
    hx_trigger_django = "reload"
    modal_form_title = _("Incomes type")
    url_name = "type_update"
    success_url = reverse_lazy("incomes:tab_types")


class Search(SearchViewMixin):
    template_name = "incomes/income_list.html"
    search_method = "search_incomes"
    per_page = 50
