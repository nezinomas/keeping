from django.http import JsonResponse
from django.template.loader import render_to_string

from ..core.lib.date import years
from ..core.mixins.ajax import AjaxCustomFormMixin
from ..core.mixins.views import (CreateAjaxMixin, DispatchAjaxMixin,
                                 IndexMixin, ListMixin, UpdateAjaxMixin)
from . import forms, models
from .apps import App_name
from .lib import views_helper as H


class ReloadStats(DispatchAjaxMixin, IndexMixin):
    template_name = f'{App_name}/includes/reload_stats.html'
    redirect_view = f'{App_name}:{App_name}_index'

    def get(self, request, *args, **kwargs):
        context = H.context_to_reload(request)
        return self.render_to_response(context)


class HistoricalData(IndexMixin):
    template_name = f'{App_name}/includes/chart_consumsion_history.html'

    def get(self, request, *args, **kwargs):
        year = request.user.year + 1
        qty = kwargs.get('qty', 0)
        chart_serries = H.several_years_consumption(range(year - qty, year))
        context = {
            'serries': chart_serries,
            'chart_container_name': 'history_chart'
        }
        rendered = render_to_string(self.template_name, context, request)

        return JsonResponse({'html': rendered})


class Compare(AjaxCustomFormMixin):
    template_name = f'{App_name}/includes/compare_form.html'
    form_class = forms.DrinkCompareForm
    form_data_dict = {}

    def form_valid(self, form):
        html = 'Trūksta duomenų'
        years_data = [self.form_data_dict['year1'], self.form_data_dict['year2']]
        chart_serries = H.several_years_consumption(years_data)

        if len(chart_serries) == 2:
            template = f'{App_name}/includes/chart_consumsion_history.html'
            context = {
                'serries': chart_serries,
                'chart_container_name': 'compare_chart'
            }
            html = render_to_string(template, context, self.request)

        data = {
            'form_is_valid': True,
            'html_form': self._render_form({'form': form}),
            'html': html,
        }
        return JsonResponse(data)


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
            **H.context_to_reload(self.request, context),
        })
        return context


class Lists(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.year

        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'data',
            'data': render_to_string(
                template_name=f'{App_name}/includes/drinks_list.html',
                context={'items': models.Drink.objects.year(year)},
                request=self.request
            ),
        })
        return context


class New(CreateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class Summary(IndexMixin):
    def get_context_data(self, **kwargs):
        qs = list(models.Drink.objects.summary())
        drink_years = [x['year'] for x in qs]

        context = super().get_context_data(**kwargs)
        context.update({
            'tab': 'history',
            'drinks_categories': drink_years,
            'drinks_data_ml': [x['per_day'] for x in qs],
            'drinks_data_alcohol': [x['qty'] * 0.025 for x in qs],
            'drinks_cnt': len(drink_years) - 1.5,
        })
        return context


class Update(UpdateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class TargetLists(ListMixin):
    model = models.DrinkTarget


class TargetNew(CreateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm


class TargetUpdate(UpdateAjaxMixin):
    model = models.DrinkTarget
    form_class = forms.DrinkTargetForm
