from datetime import date

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.chart_months import ChartMonths
from ..core.lib.convert_price import PriceToFloatViewMixin
from ..core.lib.overview_cards import OverviewCards
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
from .services.cards import LARGEST_TYPE_EXPLANATION
from .services.model_services import IncomeModelService, IncomeTypeModelService
from .services.search import search_incomes
from .services.type_rows import TypesTable
from .tabs import TABS


class TabViewMixin(CoreTabViewMixin):
    tabs = TABS
    default_tab = TABS["index"]
    app_title = _("Incomes")
    page_template = "incomes/index.html"


class TabIndex(TabViewMixin, TemplateViewMixin):
    def get_context_data(self, **kwargs):
        boundary = YearBoundary(self.request.user.selected_year(), date.today())
        service = IncomeModelService(self.request.user)

        return {
            **super().get_context_data(**kwargs),
            "cards": OverviewCards.build(
                list(service.sum_by_between("income_type", *boundary.span)),
                list(service.sum_by_between("income_type", *boundary.previous_span)),
                boundary,
                LARGEST_TYPE_EXPLANATION,
            ),
            "chart": ChartMonths.build(
                list(service.sum_by_month_between(*boundary.span)),
                list(service.sum_by_month_between(*boundary.previous_span)),
                boundary,
            ),
        }


class Lists(ListViewMixin):
    template_name = "incomes/income_list.html"

    def get_queryset(self):
        user = self.request.user
        return (
            IncomeModelService(user)
            .year(user.selected_year())
            .order_by("-date", "price")
            .values(
                "id", "date", "income_type__title", "account__title", "price", "remark"
            )
        )


class TabData(TabViewMixin, Lists):
    tab = TABS["data"]


class TabTypes(TabViewMixin, TemplateViewMixin):
    tab = TABS["types"]

    def get_context_data(self, **kwargs):
        user = self.request.user
        boundary = YearBoundary(user.selected_year(), date.today())
        service = IncomeModelService(user)
        types = IncomeTypeModelService(user).items().values("id", "title")

        return {
            **super().get_context_data(**kwargs),
            "table": TypesTable.build(
                list(types),
                list(service.sum_by_between("income_type", *boundary.span)),
                list(service.sum_by_between("income_type", *boundary.previous_span)),
                list(service.last_date_by("income_type", boundary.end_date)),
                self.request.GET.get("order", ""),
            ),
        }


# the nav and Bookkeeping open these too, so they take no tab kwarg
class New(CreateViewMixin):
    form_class = forms.IncomeForm
    success_url = reverse_lazy("incomes:tab_data")
    hx_trigger_form = "reload"
    modal_form_title = _("Incomes")


class Update(PriceToFloatViewMixin, UpdateViewMixin):
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
    search_method = staticmethod(search_incomes)
