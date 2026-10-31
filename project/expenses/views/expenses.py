from datetime import date
from functools import cached_property, partial
from typing import cast
from urllib.parse import urlencode

from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ...core.lib.convert_price import PriceToFloatViewMixin
from ...core.lib.overview_cards import Overview
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
from ..services.model_services import (
    ExpenseModelService,
    ExpenseNameModelService,
)
from ..services.month_filter import ALL, MonthFilter
from ..tabs import TABS

LARGEST_TYPE_EXPLANATION = _("The expense type with the biggest share of this year")


def month_filter(kwargs) -> MonthFilter:
    return MonthFilter.parse(kwargs["month"], date.today())


class DuomenysAtItsMonthMixin:
    def get_success_url(self):
        return MonthFilter.at(self.object.date).url()


class TabViewMixin(CoreTabViewMixin):
    tabs = TABS
    default_tab = TABS["index"]
    app_title = _("Expenses")
    page_template = "expenses/index.html"


class TabIndex(TabViewMixin, TemplateViewMixin):
    def get_context_data(self, **kwargs):
        overview = Overview.build(
            ExpenseModelService(self.request.user),
            "expense_type",
            YearBoundary(self.request.user.selected_year(), date.today()),
            LARGEST_TYPE_EXPLANATION,
        )

        return {
            **super().get_context_data(**kwargs),
            "cards": overview.cards,
            "chart": overview.chart,
        }


class TabData(TabViewMixin, TemplateViewMixin):
    tab = TABS["data"]

    def get_context_data(self, **kwargs):
        month = month_filter(self.kwargs)
        search = self.request.GET.get("search", "")
        params = {"search": search}
        if page := self.request.GET.get("page"):
            params["page"] = page

        data_url = reverse("expenses:list", args=[month.value])
        tab_url = month.url()
        if search:
            query = urlencode(params)
            data_url = f"{reverse('expenses:search')}?{query}"
            tab_url = f"{tab_url}?{query}"

        return super().get_context_data(**kwargs) | {
            "month": month,
            "items": month.items(),
            "search": search,
            "data_url": data_url,
            # a save reloads the tab at the month and search it shows
            "tab_url": tab_url,
        }


class Lists(ListViewMixin):
    template_name = "expenses/expense_list.html"

    @cached_property
    def month(self) -> MonthFilter:
        return month_filter(self.kwargs)

    @cached_property
    def user(self) -> User:
        return cast(User, self.request.user)

    def get_queryset(self):
        service = ExpenseModelService(self.user)
        qs = service.year(self.user.selected_year()).filter(**self.month.lookup())

        data = service.expenses_list(qs)

        return add_fast_urls(data=data, app_name=App_name)

    def get_context_data(self, **kwargs):
        context = {
            "month": self.month,
            "all_months": self.month.value == ALL,
            "year": self.user.selected_year(),
        }
        return super().get_context_data(**kwargs) | context | get_action_buttons_html()


class New(DuomenysAtItsMonthMixin, CreateViewMixin):
    form_class = forms.ExpenseForm
    hx_trigger_form = "reload"
    modal_form_title = _("Expenses")
    template_name = "expenses/expense_form.html"


class Update(DuomenysAtItsMonthMixin, PriceToFloatViewMixin, UpdateViewMixin):
    service_class = ExpenseModelService
    form_class = forms.ExpenseForm
    hx_trigger_django = "reload"
    modal_form_title = _("Expenses")
    template_name = "expenses/expense_form.html"


# DeleteView builds its success url before it deletes; the 204 reply discards it
class Delete(DuomenysAtItsMonthMixin, DeleteViewMixin):
    service_class = ExpenseModelService
    modal_form_title = _("Delete expense")


class Search(SearchViewMixin):
    template_name = "expenses/expense_list.html"
    search_method = staticmethod(search.search_expenses)
    search_totals = staticmethod(search.search_totals)
    search_rows = staticmethod(partial(add_fast_urls, app_name=App_name))

    def get_context_data(self, **kwargs):
        # a page link of only a query lands on the Duomenys url the search was pushed to
        return super().get_context_data(**kwargs) | {"url": ""}


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
