from datetime import datetime
from typing import cast

from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

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


class TabViewMixin:
    tab = DEFAULT_TAB

    def get_template_names(self):
        return [self.tab.template_name]

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)

        return {
            **super().get_context_data(**kwargs),
            "tab": self.tab.name,
            "drink_type_control": self.tab.control(user.drink_type),
        }

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        htmx = self.request.htmx

        if htmx and not htmx.history_restore_request:
            return response

        return render(
            self.request,
            "drinks/index.html",
            {**context, **self._page(), "content": response.rendered_content},
        )

    def _page(self) -> dict:
        """What the shell around a tab needs, and no tab does."""
        user = cast(User, self.request.user)

        return {
            "tabs": TABS,
            "recent_days": services.RecentDaySelector.for_day(datetime.now().date()),
            "drink_types": services.DrinkTypeSelector(user.drink_type),
        }


class TabIndex(TabViewMixin, TemplateViewMixin):
    tab = DrinkTab.resolve("index")

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.IndexTab.build(user, year),
        }


class TabHabits(TabViewMixin, TemplateViewMixin):
    tab = DrinkTab.resolve("habits")

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.HabitsTab.build(user, year),
        }


class TypicalYearChart(HtmxFormRetargetMixin, FormViewMixin):
    form_class = forms.TypicalYearForm
    template_name = "drinks/includes/typical_year_form.html"
    retarget = "#typical-year-form"

    def get(self, request, *args, **kwargs):
        year = cast(int, cast(User, request.user).year)
        chart = self._chart(services.PooledRange.resolve(year, self.kwargs.get("qty")))

        return self._render(chart, self.get_form(initial=self._initial(chart)))

    def form_valid(self, form, **kwargs):
        chart = self._chart(
            services.PooledRange(
                form.cleaned_data["year_from"], form.cleaned_data["year_to"]
            )
        )

        return self._render(chart, form)

    def _chart(self, pooled: services.PooledRange):
        user = cast(User, self.request.user)

        return services.TypicalYear.build(user, cast(int, user.year), pooled)

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
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.TrendsTab.build(user, year),
        }


class TabRisk(TabViewMixin, TemplateViewMixin):
    tab = DrinkTab.resolve("risk")

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.RiskTab.build(user, year),
        }


class TabData(TabViewMixin, ListViewMixin):
    service_class = DrinkModelService
    tab = DrinkTab.resolve("data")

    def get_queryset(self):
        user = cast(User, self.request.user)
        return DrinkModelService(user).year(user.year)


class TabHistory(TabViewMixin, TemplateViewMixin):
    tab = DrinkTab.resolve("history")

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **{"form": forms.DrinkCompareForm(user=self.request.user)},
            **services.history.load_service(self.request.user),
        }


class Compare(TemplateViewMixin):
    template_name = "drinks/includes/history.html"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)

        return {
            "chart": services.YearComparison.for_recent(
                user, cast(int, user.year), self.kwargs.get("qty", 0)
            ),
            "form": forms.DrinkCompareForm(user=user),
        }


class CompareTwo(HtmxFormRetargetMixin, FormViewMixin):
    form_class = forms.DrinkCompareForm
    template_name = "drinks/includes/compare_form.html"
    success_url = reverse_lazy("drinks:compare_two")
    retarget = "#compare-form"

    def form_valid(self, form, **kwargs):
        chart = services.YearComparison.for_pair(
            self.request.user,
            form.cleaned_data["year1"],
            form.cleaned_data["year2"],
        )

        return render(
            self.request,
            "drinks/includes/history.html",
            {"form": form, "chart": chart},
        )


class New(CreateViewMixin):
    service_class = DrinkModelService
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
    service_class = DrinkTargetModelService
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


class SelectDrink(RedirectViewMixin):
    def get(self, request, *args, **kwargs):
        drink_type = kwargs["drink_type"]

        if drink_type not in models.DrinkType.values:
            raise Http404

        user = cast(User, request.user)
        user.drink_type = drink_type
        user.save()

        if not request.htmx:
            return super().get(request, *args, **kwargs)

        # stay on the tab the change was fired from
        return tab_reload_response(request.GET.get("tab"))

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy("drinks:index")


class QuickAdd(View):
    def post(self, request, *args, **kwargs):
        form = forms.QuickAddForm.from_post(request.POST, cast(User, request.user))

        if not form.is_valid():
            return HttpResponse(status=422)

        form.save()

        return tab_reload_response(request.POST.get("tab"))
