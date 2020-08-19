import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.template.loader import render_to_string
from django.views.generic.edit import FormView

from ..core.lib.date import years
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


class Compare(LoginRequiredMixin, FormView):
    template_name = f'{App_name}/includes/compare_form.html'
    form_class = forms.DrinkCompareForm
    form_data_dict = {}

    def post(self, request, *args, **kwargs):
        err = {'error': 'CompareForm is broken.'}
        try:
            form_data = request.POST['form_data']
        except KeyError:
            return JsonResponse(data=err, status=404)

        try:
            form_data_list = json.loads(form_data)

            # flatten list of dictionaries - form_data_list
            for field in form_data_list:
                self.form_data_dict[field["name"]] = field["value"]

        except (json.decoder.JSONDecodeError, KeyError):
            return JsonResponse(data=err, status=500)

        form = self.form_class(self.form_data_dict)
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form, **kwargs)

    def form_invalid(self, form):
        data = {
            'form_is_valid': False,
            'html_form': self._render_form({'form': form}),
            'html': None,
        }
        return JsonResponse(data)

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

    def _render_form(self, context):
        return (
            render_to_string(self.template_name, context, request=self.request)
        )


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
