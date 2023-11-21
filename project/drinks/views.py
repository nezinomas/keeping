from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..core.lib.translation import month_names
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    FormViewMixin,
    ListViewMixin,
    RedirectViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from . import services
from .forms import DrinkCompareForm, DrinkForm, DrinkTargetForm
from .lib.drinks_options import DrinksOptions
from .models import Drink, DrinkTarget, DrinkType


class Index(TemplateViewMixin):
    template_name = "drinks/index.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **services.helper.drink_type_dropdown(self.request),
        }


class TabIndex(TemplateViewMixin):
    template_name = "drinks/tab_index.html"

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        context = services.index.load_service(year)

        return super().get_context_data(**kwargs) | context


class TabData(ListViewMixin):
    model = Drink
    template_name = "drinks/tab_data.html"

    def get_queryset(self):
        year = self.request.user.year
        return Drink.objects.year(year=year)


class TabHistory(TemplateViewMixin):
    template_name = "drinks/tab_history.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **services.history.load_service(),
        }


class Compare(TemplateViewMixin):
    template_name = "drinks/includes/history.html"

    def get_context_data(self, **kwargs):
        year = self.request.user.year + 1
        qty = self.kwargs.get("qty", 0)
        chart_serries = services.helper.several_years_consumption(
            range(year - qty, year)
        )
        return {
            "chart": {
                "categories": list(month_names().values()),
                "serries": chart_serries,
            },
        }


class CompareTwo(FormViewMixin):
    form_class = DrinkCompareForm
    template_name = "drinks/includes/compare_form.html"
    success_url = reverse_lazy("drinks:compare_two")

    def form_valid(self, form, **kwargs):
        context = {}
        year1 = form.cleaned_data["year1"]
        year2 = form.cleaned_data["year2"]
        chart_serries = services.helper.several_years_consumption([year1, year2])

        if len(chart_serries) == 2:
            context |= {
                "form": form,
                "chart": {
                    "categories": list(month_names().values()),
                    "serries": chart_serries,
                },
            }
        return render(self.request, self.template_name, context)


class New(CreateViewMixin):
    model = Drink
    form_class = DrinkForm
    success_url = reverse_lazy("drinks:tab_data")

    def get_hx_trigger_django(self):
        tab = self.kwargs.get("tab")

        if tab in ["index", "data", "history"]:
            return f"reload{tab.title()}"

        return "reloadData"

    def url(self):
        tab = self.kwargs.get("tab")

        if tab not in ["index", "data", "history"]:
            tab = "index"

        return reverse_lazy("drinks:new", kwargs={"tab": tab})


class Update(UpdateViewMixin):
    model = Drink
    form_class = DrinkForm
    hx_trigger_django = "reloadData"
    success_url = reverse_lazy("drinks:tab_data")

    def get_object(self):
        obj = super().get_object()

        if obj:
            obj.quantity = obj.quantity * DrinksOptions(drink_type=obj.option).ratio

        return obj


class Delete(DeleteViewMixin):
    model = Drink
    hx_trigger_django = "reloadData"
    success_url = reverse_lazy("drinks:tab_data")


class TargetLists(ListViewMixin):
    model = DrinkTarget

    def get_queryset(self):
        year = self.request.user.year
        return super().get_queryset().year(year)


class TargetNew(CreateViewMixin):
    model = DrinkTarget
    form_class = DrinkTargetForm
    success_url = reverse_lazy("drinks:index")

    def get_hx_trigger_django(self):
        tab = self.kwargs.get("tab")

        if tab in ["index", "data", "history"]:
            return f"reload{tab.title()}"

        return "reloadIndex"

    def url(self):
        tab = self.kwargs.get("tab")

        if tab not in ["index", "data", "history"]:
            tab = "index"

        return reverse_lazy("drinks:target_new", kwargs={"tab": tab})


class TargetUpdate(UpdateViewMixin):
    model = DrinkTarget
    form_class = DrinkTargetForm
    hx_trigger_django = "reloadIndex"
    success_url = reverse_lazy("drinks:tab_index")

    def get_object(self):
        obj = super().get_object()

        if obj:
            if obj.drink_type == "stdav":
                return obj

            obj.quantity = DrinksOptions().stdav_to_ml(
                drink_type=obj.drink_type, stdav=obj.quantity
            )

        return obj


class SelectDrink(RedirectViewMixin):
    def get_redirect_url(self, *args, **kwargs):
        drink_type = kwargs.get("drink_type")

        if drink_type not in DrinkType.values:
            drink_type = DrinkType.BEER.value

        user = self.request.user
        user.drink_type = drink_type
        user.save()

        return reverse_lazy("drinks:index")
