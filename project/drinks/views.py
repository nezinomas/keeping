from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.translation import month_names
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    FormViewMixin,
    ListViewMixin,
    RedirectViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
    rendered_content,
)
from . import forms, models, services
from .lib.drinks_options import DrinksOptions


class Index(TemplateViewMixin):
    template_name = "drinks/index.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **{"content": rendered_content(self.request, TabIndex, **kwargs)},
        }


class TabIndex(TemplateViewMixin):
    template_name = "drinks/tab_index.html"

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        return {
            **super().get_context_data(**kwargs),
            **{
                "tab": "index",
                "target": rendered_content(self.request, TargetLists, **kwargs),
            },
            **services.helper.drink_type_dropdown(self.request),
            **services.index.load_service(year),
        }


class TabData(ListViewMixin):
    model = models.Drink
    template_name = "drinks/tab_data.html"

    def get_queryset(self):
        year = self.request.user.year
        return models.Drink.objects.year(year=year)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **{"tab": "data"},
            **services.helper.drink_type_dropdown(self.request),
        }


class TabHistory(TemplateViewMixin):
    template_name = "drinks/tab_history.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **{"tab": "history"},
            **services.helper.drink_type_dropdown(self.request),
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
    form_class = forms.DrinkCompareForm
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
    model = models.Drink
    form_class = forms.DrinkForm
    success_url = reverse_lazy("drinks:tab_data")
    template_name = "core/generic_form.html"
    form_title = _('Drinks')

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
    model = models.Drink
    form_class = forms.DrinkForm
    hx_trigger_django = "reloadData"
    success_url = reverse_lazy("drinks:tab_data")
    template_name = "core/generic_form.html"
    form_title = _('Drinks')

    def get_object(self):
        obj = super().get_object()

        if obj:
            obj.quantity = obj.quantity * DrinksOptions(drink_type=obj.option).ratio

        return obj


class Delete(DeleteViewMixin):
    model = models.Drink
    hx_trigger_django = "reloadData"
    success_url = reverse_lazy("drinks:tab_data")
    template_name = "core/generic_delete_form.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"title": _("Delete drinks")}


class TargetLists(ListViewMixin):
    model = models.DrinkTarget

    def get_queryset(self):
        year = self.request.user.year
        return super().get_queryset().year(year)


class TargetNew(CreateViewMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm
    success_url = reverse_lazy("drinks:index")
    template_name = "core/generic_form.html"
    form_title = _('Goal for the year')

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
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm
    hx_trigger_django = "reloadIndex"
    success_url = reverse_lazy("drinks:tab_index")
    template_name = "core/generic_form.html"
    form_title = _('Goal for the year')

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

        if drink_type not in models.DrinkType.values:
            drink_type = models.DrinkType.BEER.value

        user = self.request.user
        user.drink_type = drink_type
        user.save()

        return reverse_lazy("drinks:index")
