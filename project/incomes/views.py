from django.urls import reverse_lazy
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import ConvertPriceMixin
from ..core.lib.year_boundary import YearBoundary
from ..core.mixins.tabs import TabViewMixin as CoreTabViewMixin
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
from .services.type_rows import TypesTable
from .tabs import DEFAULT_TAB, TABS, IncomeTab


class TabViewMixin(CoreTabViewMixin):
    tab = DEFAULT_TAB
    fragment_template = "incomes/tab_fragment.html"
    page_template = "incomes/index.html"

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "tab_url": self.tab.url}

    def page_context(self) -> dict:
        return {
            "page_title": format_lazy("{} | {}", _("Incomes"), self.tab.title),
            "tabs": [(tab, tab.url) for tab in TABS],
        }


class TabIndex(TabViewMixin, TemplateViewMixin):
    tab = IncomeTab.resolve("index")

    def get_context_data(self, **kwargs):
        boundary = YearBoundary.for_year(self.request.user.year)
        service = IncomeModelService(self.request.user)

        return {
            **super().get_context_data(**kwargs),
            "cards": OverviewCards.build(
                list(service.sum_by_type_between(*boundary.span)),
                list(service.sum_by_type_between(*boundary.previous_span)),
                boundary,
            ),
            "chart": ChartMonths.build(
                list(service.sum_by_month_between(*boundary.span)),
                list(service.sum_by_month_between(*boundary.previous_span)),
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


class TabTypes(TabViewMixin, TemplateViewMixin):
    tab = IncomeTab.resolve("types")

    def get_context_data(self, **kwargs):
        user = self.request.user
        boundary = YearBoundary.for_year(user.year)
        service = IncomeModelService(user)
        types = IncomeTypeModelService(user).items().values("id", "title")

        return {
            **super().get_context_data(**kwargs),
            "table": TypesTable.build(
                list(types),
                list(service.sum_by_type_between(*boundary.span)),
                list(service.sum_by_type_between(*boundary.previous_span)),
                list(service.last_date_by_type(boundary.end_date)),
                self.request.GET.get("order", ""),
            ),
        }


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
