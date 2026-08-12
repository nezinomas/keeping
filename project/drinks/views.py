from datetime import datetime
from typing import cast

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from django_htmx.http import trigger_client_event

from ..core.lib.date import set_date_with_user_year
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
    tab = DEFAULT_TAB

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)

        return {
            **super().get_context_data(**kwargs),
            "tab": self.tab,
            "drink_type_control": services.control_for_tab(self.tab, user.drink_type),
        }


class TabViewMixin(DrinkTypeContextMixin):
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
            "tabs": DrinkTabs.all(),
            "recent_days": services.RecentDaySelector.for_day(datetime.now().date()),
            "drink_types": services.DrinkTypeSelector(user.drink_type),
        }


class TabIndex(TabViewMixin, TemplateViewMixin):
    template_name = "drinks/tab_index.html"
    tab = "index"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.IndexTab.build(user, year),
        }


class TabHabits(TabViewMixin, TemplateViewMixin):
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


class TabTrends(TabViewMixin, TemplateViewMixin):
    template_name = "drinks/tab_trends.html"
    tab = "trends"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.TrendsTab.build(user, year),
        }


class TabRisk(TabViewMixin, TemplateViewMixin):
    template_name = "drinks/tab_risk.html"
    tab = "risk"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)

        return {
            **super().get_context_data(**kwargs),
            **services.RiskTab.build(user, year),
        }


class TabData(TabViewMixin, ListViewMixin):
    service_class = DrinkModelService
    template_name = "drinks/tab_data.html"
    tab = "data"

    def get_queryset(self):
        user = cast(User, self.request.user)
        return DrinkModelService(user).year(user.year)


class TabHistory(TabViewMixin, TemplateViewMixin):
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
        context = {"form": form}
        years = [form.cleaned_data["year1"], form.cleaned_data["year2"]]
        chart = services.YearComparison.build(self.request.user, years)

        if len(chart.serries) == len(years):
            context["chart"] = chart

        return render(self.request, "drinks/includes/history.html", context)

    def form_invalid(self, form):
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
