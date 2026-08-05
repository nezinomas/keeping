from datetime import datetime
from typing import cast

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from django_htmx.http import trigger_client_event

from ..core.lib.date import set_date_with_user_year
from ..core.lib.utils import rendered_content
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
from .tabs import DEFAULT_TAB, DrinkTabs


class DrinkTypeContextMixin:
    """Names the tab, and puts the drink-type control that tab wears with it.

    Which of the three controls a tab gets — the switcher, a fixed Std Av, or
    nothing — is the selector's call; a view only says which tab it is. Every
    tab response carries it, because the control lives beside the quick-add
    form, outside the swapped body, and is replaced out of band.
    """

    tab = DEFAULT_TAB

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)

        return {
            **super().get_context_data(**kwargs),
            "tab": self.tab,
            "drink_type_control": services.DrinkTypeSelector.for_tab(
                self.tab, user.drink_type
            ),
        }


class Index(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/index.html"

    def get_context_data(self, **kwargs):
        # the quick-add sheet lives on this page only, outside the tabs
        recent_days = services.RecentDaySelector.for_day(datetime.now().date())
        user = cast(User, self.request.user)
        # the quick-add form logs any drink type, whatever the open tab reads in
        drink_types = services.DrinkTypeSelector.for_drink_type(user.drink_type)

        return {
            **super().get_context_data(**kwargs),
            **{"reload_targets": DrinkTabs.all()},
            **{"recent_days": recent_days},
            **{"drink_types": drink_types},
            **{"content": rendered_content(self.request, TabIndex, **kwargs)},
        }


class TabIndex(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/tab_index.html"
    tab = "index"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.IndexTab.build(user, year),
        }


class TabHabits(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/tab_habits.html"
    tab = "habits"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.HabitsTab.build(user, year),
        }


class TypicalYearChart(FormViewMixin):
    form_class = forms.TypicalYearForm
    template_name = "drinks/includes/typical_year_form.html"

    def get(self, request, *args, **kwargs):
        user = cast(User, request.user)
        chart = services.TypicalYear.build(
            user, cast(int, user.year), self._preset_range(user)
        )

        return self._render(chart, self.get_form(initial=self._initial(chart)))

    def _preset_range(self, user) -> services.PooledRange:
        """What the press asked to pool: the last `qty` years, every year, or —
        when no preset was pressed at all — nothing."""
        if "qty" not in self.kwargs:
            return services.NoPooledRange()

        qty = self.kwargs["qty"]
        if not qty:
            return services.PooledRange()

        year = cast(int, user.year)
        return services.PooledRange(year - qty + 1, year)

    @staticmethod
    def _initial(chart) -> dict:
        if not chart.pooled.has_data:
            return {}

        return {"year_from": chart.year_from, "year_to": chart.year_to}

    def form_valid(self, form, **kwargs):
        user = cast(User, self.request.user)
        chart = services.TypicalYear.build(
            user,
            cast(int, user.year),
            services.PooledRange(
                form.cleaned_data["year_from"], form.cleaned_data["year_to"]
            ),
        )

        return self._render(chart, form)

    def form_invalid(self, form):
        # re-render the form (with errors) in place, leaving the chart untouched
        response = super().form_invalid(form)
        response["HX-Retarget"] = "#typical-year-form"
        response["HX-Reswap"] = "outerHTML"
        return response

    def _render(self, chart, form) -> HttpResponse:
        return render(
            self.request,
            "drinks/includes/typical_year.html",
            {"chart": chart, "form": form},
        )


class TabTrends(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/tab_trends.html"
    tab = "trends"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.TrendsTab.build(user, year),
        }


class TabRisk(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/tab_risk.html"
    tab = "risk"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.RiskTab.build(user, year),
        }


class TabData(DrinkTypeContextMixin, ListViewMixin):
    service_class = DrinkModelService
    template_name = "drinks/tab_data.html"
    tab = "data"

    def get_queryset(self):
        user = cast(User, self.request.user)
        return DrinkModelService(user).year(user.year)


class TabHistory(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/tab_history.html"
    tab = "history"

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
        year = cast(int, user.year) + 1
        qty = self.kwargs.get("qty", 0)

        return {
            "chart": services.YearComparison.build(user, range(year - qty, year)),
            "form": forms.DrinkCompareForm(user=self.request.user),
        }


class CompareTwo(FormViewMixin):
    form_class = forms.DrinkCompareForm
    template_name = "drinks/includes/compare_form.html"
    success_url = reverse_lazy("drinks:compare_two")

    def form_valid(self, form, **kwargs):
        # a valid submit only updates the shared history chart; the form stays
        # put in the header, so render just the chart data into its container
        context = {"form": form}
        years = [form.cleaned_data["year1"], form.cleaned_data["year2"]]
        chart = services.YearComparison.build(self.request.user, years)

        # only plot a comparison when both years actually had records
        if len(chart.serries) == len(years):
            context["chart"] = chart

        return render(self.request, "drinks/includes/history.html", context)

    def form_invalid(self, form):
        # re-render the form (with errors) in place, leaving the chart untouched
        response = super().form_invalid(form)
        response["HX-Retarget"] = "#compare-form"
        response["HX-Reswap"] = "outerHTML"
        return response


class New(CreateViewMixin):
    service_class = DrinkModelService
    form_class = forms.DrinkForm
    success_url = reverse_lazy("drinks:tab_data")
    modal_form_title = _("Drinks")

    def get_hx_trigger_django(self):
        # a new drink lands in the Data tab unless it came from another one
        return DrinkTabs.resolve(self.kwargs.get("tab"), default="data").reload_trigger

    def url(self):
        return DrinkTabs.resolve(self.kwargs.get("tab")).form_url("drinks:new")


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


class TargetLists(ListViewMixin):
    template_name = "drinks/drinktarget_list.html"
    service_class = DrinkTargetModelService

    def get_queryset(self):
        user = cast(User, self.request.user)
        return DrinkTargetModelService(user).targets(user.year)


class TargetNew(CreateViewMixin):
    service_class = DrinkTargetModelService
    form_class = forms.DrinkTargetForm
    success_url = reverse_lazy("drinks:index")
    modal_form_title = _("New goal")

    def get_hx_trigger_django(self):
        # a new goal lands in the Overview tab unless it came from another one
        return DrinkTabs.resolve(self.kwargs.get("tab")).reload_trigger

    def url(self):
        return DrinkTabs.resolve(self.kwargs.get("tab")).form_url("drinks:target_new")


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
            # the form edits the volume the user originally typed
            obj.quantity = obj.amount.value

        return obj


class SelectDrink(RedirectViewMixin):
    def get(self, request, *args, **kwargs):
        drink_type = kwargs.get("drink_type")

        if drink_type not in models.DrinkType.values:
            drink_type = models.DrinkType.BEER.value

        user = cast(User, request.user)
        user.drink_type = cast(str, drink_type)
        user.save()

        if not request.htmx:
            return super().get(request, *args, **kwargs)

        # stay on the tab the change was fired from
        trigger = DrinkTabs.resolve(request.GET.get("tab")).reload_trigger

        response = HttpResponse(status=204)
        trigger_client_event(response=response, name=trigger, params={})
        return response

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy("drinks:index")


class QuickAdd(View):
    def post(self, request, *args, **kwargs):
        user = cast(User, request.user)
        option = request.POST.get("option") or user.drink_type
        date = request.POST.get("date") or set_date_with_user_year(user)

        form = forms.DrinkForm(
            data={
                "user": user.pk,
                "date": date,
                "option": option,
                "stdav": request.POST.get("quantity"),
            },
            user=user,
        )

        if not form.is_valid():
            return HttpResponse(status=422)

        form.save()

        trigger = DrinkTabs.resolve(request.POST.get("tab")).reload_trigger

        response = HttpResponse(status=204)
        trigger_client_event(response=response, name=trigger, params={})
        return response
