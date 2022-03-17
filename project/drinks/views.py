from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import RedirectView

from ..core.lib.date import years
from ..core.mixins.ajax import AjaxSearchMixin
from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchAjaxMixin, DispatchListsMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models
from .apps import App_name
from .lib import views_helper as H
from .lib.drinks_options import DrinksOptions


class ReloadStats(DispatchAjaxMixin, IndexMixin):
    template_name = f'{App_name}/index.html'
    redirect_view = reverse_lazy(f'{App_name}:{App_name}_index')

    def get(self, request, *args, **kwargs):
        context = {}
        context.update({
            'target_list': TargetLists.as_view()(self.request, as_string=True),
            **H.RenderContext(request).context_to_reload()
        })

        return JsonResponse(context)


class HistoricalData(IndexMixin):
    template_name = f'{App_name}/includes/chart_compare.html'

    def get(self, request, *args, **kwargs):
        year = request.user.year + 1
        qty = kwargs.get('qty', 0)
        chart_serries = H.several_years_consumption(range(year - qty, year))
        context = {
            'serries': chart_serries,
            'chart_container_name': 'history_chart',
        }
        rendered = render_to_string(self.template_name, context, request)

        return JsonResponse({'html': rendered})


class Compare(AjaxSearchMixin):
    template_name = f'{App_name}/includes/compare_form.html'
    form_class = forms.DrinkCompareForm
    form_data_dict = {}

    def form_valid(self, form, **kwargs):
        html = _('No data')
        years_data = [self.form_data_dict['year1'], self.form_data_dict['year2']]
        chart_serries = H.several_years_consumption(years_data)

        if len(chart_serries) == 2:
            template = f'{App_name}/includes/chart_compare.html'
            context = {
                'serries': chart_serries,
                'chart_container_name': 'compare_chart',
            }
            html = render_to_string(template, context, self.request)

        kwargs.update({'html': html})

        return super().form_valid(form, **kwargs)


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'index',
            'all_years': len(years()),
            'compare_form': render_to_string(
                template_name=f'{App_name}/includes/compare_form.html',
                context={'form': forms.DrinkCompareForm()},
                request=self.request
            ),
            'target_list': TargetLists.as_view()(self.request, as_string=True),
            **H.drink_type_dropdown(self.request),
            **H.RenderContext(self.request).context_to_reload(),
        })
        return context


class Lists(ListMixin):
    template_name = 'drinks/index.html'
    model = models.Drink

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'data',
            **H.drink_type_dropdown(self.request),
        })

        return context


class New(CreateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class Summary(IndexMixin):
    def get_context_data(self, **kwargs):
        drink_years = []
        ml = []
        alcohol = []

        qs = list(models.Drink.objects.summary())

        obj = DrinksOptions()
        ratio = obj.ratio

        if qs:
            for year in range(qs[0]['year'], datetime.now().year+1):
                drink_years.append(year)

                item = next((x for x in qs if x['year'] == year), False)
                if item:
                    _stdav = item['qty'] / ratio
                    _alkohol = obj.stdav_to_alkohol(stdav=_stdav)

                    alcohol.append(_alkohol)
                    ml.append(item['per_day'])
                else:
                    alcohol.append(0.0)
                    ml.append(0.0)

        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'history',
            'drinks_categories': drink_years,
            'drinks_data_ml': ml,
            'drinks_data_alcohol': alcohol,
            'records': len(drink_years) if len(drink_years) > 1 else 0,
            **H.drink_type_dropdown(self.request),
        })
        return context


class Update(UpdateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm

    def get_object(self):
        obj = super().get_object()

        if obj:
            obj.quantity = obj.quantity * DrinksOptions(drink_type=obj.option).ratio

        return obj


class Delete(DeleteAjaxMixin):
    model = models.Drink


class TargetLists(DispatchListsMixin, ListMixin):
    model = models.DrinkTarget
    list_render_output = False

    def get_queryset(self):
        obj = DrinksOptions()
        year = self.request.user.year

        qs = models.DrinkTarget.objects.year(year)
        for q in qs:
            _qty = q.quantity
            q.quantity = obj.stdav_to_ml(stdav=_qty)
            q.max_bottles = obj.stdav_to_bottles(year=year, max_stdav=_qty)

        return qs

class TargetNew(CreateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm
    list_render_output = False


class TargetUpdate(UpdateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm
    list_render_output = False

    def get_object(self):
        obj = super().get_object()

        if obj:
            if obj.drink_type ==  'stdav':
                return obj

            obj.quantity = (
                DrinksOptions().stdav_to_ml(drink_type=obj.drink_type,
                                            stdav=obj.quantity)
            )

        return obj


class SelectDrink(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        drink_type = kwargs.get('drink_type')

        if drink_type not in models.DrinkType.values:
            drink_type = models.DrinkType.BEER.value

        user = self.request.user
        user.drink_type = drink_type
        user.save()

        return reverse_lazy('drinks:drinks_index')
