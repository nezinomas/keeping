from functools import cached_property
from typing import cast

from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from ..core.mixins.kwargs import TodayMixin
from ..core.mixins.tabs import TabViewMixin as CoreTabViewMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    FormViewMixin,
    ListViewMixin,
    RedirectViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from ..users.models import User
from . import forms, models, services
from .services.model_services import DrinkModelService, DrinkTargetModelService
from .tabs import DEFAULT_TAB, TABS, DrinkTab, tab_reload_response


class HtmxFormRetargetMixin:
    """The target swapped on success is the chart, so the errors have to be
    retargeted at the form's own wrapper."""

    retarget = ""

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response["HX-Retarget"] = self.retarget
        response["HX-Reswap"] = "outerHTML"

        return response


class UserMixin:
    @cached_property
    def user(self) -> User:
        return cast(User, self.request.user)


class TabViewMixin(UserMixin, TodayMixin, CoreTabViewMixin):
    tab = DEFAULT_TAB
    fragment_template = "drinks/tab_fragment.html"
    page_template = "drinks/index.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "drink_type_control": self.tab.control(self.user.drink_type),
        }

    def page_context(self) -> dict:
        """What the shell around a tab needs, and no tab does."""
        return {
            "tab_title": self.tab.title,
            "page_title": format_lazy("{} | {}", _("Drinks"), self.tab.title),
            "tabs": [(tab, tab.url) for tab in TABS],
            "recent_days": services.RecentDaySelector.for_day(self.today),
            "drink_types": services.DrinkTypeSelector(self.user.drink_type),
        }


class TabIndex(TabViewMixin, TemplateViewMixin):
    tab = DrinkTab.resolve("index")

    def get_context_data(self, **kwargs):
        year = self.user.selected_year()

        return {
            **super().get_context_data(**kwargs),
            **services.IndexTab.build(self.user, year, self.today),
        }


class TabHabits(TabViewMixin, TemplateViewMixin):
    tab = DrinkTab.resolve("habits")

    def get_context_data(self, **kwargs):
        year = self.user.selected_year()

        return {
            **super().get_context_data(**kwargs),
            **services.HabitsTab.build(self.user, year, self.today),
        }


class TypicalYearChart(UserMixin, HtmxFormRetargetMixin, FormViewMixin):
    form_class = forms.TypicalYearForm
    template_name = "drinks/includes/typical_year_form.html"
    retarget = "#typical-year-form"

    def get(self, request, *args, **kwargs):
        year = self.user.selected_year()
        pooled = services.NoPooledRange()
        if "qty" in self.kwargs:
            pooled = services.PooledRange.resolve(year, self.kwargs["qty"])

        chart = self._chart(pooled)

        return self._render(chart, self.get_form(initial=self._initial(chart)))

    def form_valid(self, form):
        chart = self._chart(
            services.PooledRange(
                form.cleaned_data["year_from"], form.cleaned_data["year_to"]
            )
        )

        return self._render(chart, form)

    def _chart(self, pooled: services.PooledRange):
        return services.TypicalYear.build(
            self.user, self.user.selected_year(), self.today, pooled
        )

    @staticmethod
    def _initial(chart) -> dict:
        if not chart.pooled.has_data:
            return {}

        return {"year_from": chart.year_from, "year_to": chart.year_to}

    def _render(self, chart, form) -> HttpResponse:
        return render(
            self.request,
            "drinks/includes/typical_year.html",
            {"chart": chart, "form": form},
        )


class TabTrends(TabViewMixin, TemplateViewMixin):
    tab = DrinkTab.resolve("trends")

    def get_context_data(self, **kwargs):
        year = self.user.selected_year()

        return {
            **super().get_context_data(**kwargs),
            **services.TrendsTab.build(self.user, year, self.today),
        }


class TabRisk(TabViewMixin, TemplateViewMixin):
    tab = DrinkTab.resolve("risk")

    def get_context_data(self, **kwargs):
        year = self.user.selected_year()

        return {
            **super().get_context_data(**kwargs),
            **services.RiskTab.build(self.user, year, self.today),
        }


class TabData(TabViewMixin, ListViewMixin):
    tab = DrinkTab.resolve("data")

    def get_queryset(self):
        return DrinkModelService(self.user).year(self.user.selected_year())


class TabHistory(TabViewMixin, TemplateViewMixin):
    tab = DrinkTab.resolve("history")

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "form": forms.DrinkCompareForm(user=self.user, today=self.today),
            **services.history.load_service(self.user, self.today),
        }


class Compare(UserMixin, TodayMixin, TemplateViewMixin):
    template_name = "drinks/includes/history.html"

    def get_context_data(self, **kwargs):
        return {
            "chart": services.YearComparison.for_recent(
                self.user,
                self.user.selected_year(),
                self.kwargs.get("qty", 0),
                self.today,
            ),
            "form": forms.DrinkCompareForm(user=self.user, today=self.today),
        }


class CompareTwo(UserMixin, HtmxFormRetargetMixin, FormViewMixin):
    form_class = forms.DrinkCompareForm
    template_name = "drinks/includes/compare_form.html"
    success_url = reverse_lazy("drinks:compare_two")
    retarget = "#compare-form"

    def form_valid(self, form):
        chart = services.YearComparison.for_pair(
            self.user,
            form.cleaned_data["year1"],
            form.cleaned_data["year2"],
            self.today,
        )

        return render(
            self.request,
            "drinks/includes/history.html",
            {"form": form, "chart": chart},
        )


class New(CreateViewMixin):
    form_class = forms.DrinkForm
    success_url = reverse_lazy("drinks:tab_data")
    modal_form_title = _("Drinks")

    def get_hx_trigger_django(self):
        return DrinkTab.resolve(self.kwargs.get("tab"), default="data").reload_trigger

    def url(self):
        return DrinkTab.resolve(self.kwargs.get("tab")).form_url("drinks:new")


class Update(UpdateViewMixin):
    service_class = DrinkModelService
    form_class = forms.DrinkForm
    hx_trigger_django = "reloadData"
    success_url = reverse_lazy("drinks:tab_data")
    modal_form_title = _("Drinks")


class Delete(DeleteViewMixin):
    service_class = DrinkModelService
    hx_trigger_django = "reloadData"
    success_url = reverse_lazy("drinks:tab_data")
    modal_form_title = _("Delete drinks")


class TargetNew(CreateViewMixin):
    form_class = forms.DrinkTargetForm
    success_url = reverse_lazy("drinks:index")
    modal_form_title = _("New goal")

    def get_hx_trigger_django(self):
        return DrinkTab.resolve(self.kwargs.get("tab")).reload_trigger

    def url(self):
        return DrinkTab.resolve(self.kwargs.get("tab")).form_url("drinks:target_new")


class TargetUpdate(UpdateViewMixin):
    service_class = DrinkTargetModelService
    form_class = forms.DrinkTargetForm
    hx_trigger_django = "reloadIndex"
    url_name = "target_update"
    success_url = reverse_lazy("drinks:tab_index")
    modal_form_title = _("Update goal")

    def get_object(self):
        obj = super().get_object()

        if obj:
            obj.quantity = obj.amount.value

        return obj


class SelectDrink(UserMixin, RedirectViewMixin):
    def get(self, request, *args, **kwargs):
        drink_type = kwargs["drink_type"]

        if drink_type not in models.DrinkType.values:
            raise Http404

        self.user.drink_type = drink_type
        self.user.save()

        if not request.htmx:
            return super().get(request, *args, **kwargs)

        # stay on the tab the change was fired from
        return tab_reload_response(request.GET.get("tab"))

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy("drinks:index")


class QuickAdd(UserMixin, TodayMixin, View):
    def post(self, request, *args, **kwargs):
        form = forms.QuickAddForm.from_post(request.POST, self.user, self.today)

        if not form.is_valid():
            return HttpResponse(status=422)

        form.save()

        return tab_reload_response(request.POST.get("tab"))
