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
from .tabs import DrinkTabs


class DrinkTypeContextMixin:
    """Puts the drink-type switcher into the context of every drinks tab."""

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)

        return {
            **super().get_context_data(**kwargs),
            "drink_types": services.DrinkTypeSelector.for_drink_type(user.drink_type),
        }


class Index(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/index.html"

    def get_context_data(self, **kwargs):
        # the quick-add sheet lives on this page only, outside the tabs
        recent_days = services.RecentDaySelector.for_day(datetime.now().date())

        return {
            **super().get_context_data(**kwargs),
            **{"reload_targets": DrinkTabs.all()},
            **{"recent_days": recent_days},
            **{"content": rendered_content(self.request, TabIndex, **kwargs)},
        }


class TabIndex(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/tab_index.html"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **{"tab": "index"},
            **services.IndexTab.build(user, year),
        }


class TabHabits(DrinkTypeContextMixin, TemplateViewMixin):
    # every figure on this tab is a count, a ratio or a Std Av harm metric, so
    # none of them follows the dropdown — but the dropdown is in the navbar of
    # every tab, so the mixin that fills it is not optional here either
    template_name = "drinks/tab_habits.html"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **{"tab": "habits"},
            **services.HabitsTab.build(user, year),
        }


class TypicalYearChart(FormViewMixin):
    """The pooled typical-year chart on the Habits tab, and the range form that
    re-pools it.

    A partial rather than part of the tab: the Habits container fetches this on
    load and re-fetches it on every submit, so the chart, its caption and the
    form's own boxes are always the same reading of the same range. Nothing is
    remembered between fetches — a fresh tab opens on the full span, which is
    the only default the app can claim to know.
    """

    form_class = forms.TypicalYearForm
    template_name = "drinks/includes/typical_year_form.html"

    def get(self, request, *args, **kwargs):
        chart = services.TypicalYear.build(cast(User, request.user))
        initial = (
            {"year_from": chart.year_from, "year_to": chart.year_to}
            if chart.has_data
            else {}
        )

        return self._render(chart, self.get_form(initial=initial))

    def form_valid(self, form, **kwargs):
        chart = services.TypicalYear.build(
            cast(User, self.request.user),
            form.cleaned_data["year_from"],
            form.cleaned_data["year_to"],
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

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **{"tab": "trends"},
            **services.TrendsTab.build(user, year),
        }


class TabRisk(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/tab_risk.html"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **{"tab": "risk"},
            **services.RiskTab.build(user, year),
        }


class TabData(DrinkTypeContextMixin, ListViewMixin):
    service_class = DrinkModelService
    template_name = "drinks/tab_data.html"

    def get_queryset(self):
        user = cast(User, self.request.user)
        return DrinkModelService(user).year(user.year)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **{"tab": "data"},
        }


class TabHistory(DrinkTypeContextMixin, TemplateViewMixin):
    template_name = "drinks/tab_history.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **{"tab": "history"},
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
