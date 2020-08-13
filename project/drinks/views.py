import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from ..core.lib.date import years
from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models
from .apps import App_name
from .lib import views_helper as H


class ReloadStats(TemplateView):
    template_name = f'{App_name}/includes/reload_stats.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            request.GET['ajax_trigger']
        except KeyError:
            return redirect(reverse(f'{App_name}:{App_name}_index'))

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = H.context_to_reload(request)
        return self.render_to_response(context)


class HistoricalData(IndexMixin):
    template_name = f'{App_name}/includes/chart_consumsion_history.html'

    def get(self, request, *args, **kwargs):
        year = request.user.year + 1
        qty = kwargs.get('qty', 0)
        chart_serries = H.several_years_consumption(range(year - qty, year))

        context = {'serries': chart_serries, 'chart_container_name': 'history_chart'}
        rendered = render_to_string(self.template_name, context, request)

        return JsonResponse({'html': rendered})


@login_required()
def compare(request):
    try:
        form_data = request.POST['form_data']
    except KeyError:
        return JsonResponse({'error': 'CompareForm is broken.'}, status=404)

    try:
        form_data_dict = {}
        form_data_list = json.loads(form_data)

        # flatten list of dictionaries - form_data_list
        for field in form_data_list:
            form_data_dict[field["name"]] = field["value"]
    except (json.decoder.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'CompareForm is broken.'}, status=500)

    chart_serries = []
    form = forms.DrinkCompareForm(data=form_data_dict)
    json_data = {
        'form_is_valid': False,
        'html_form': render_to_string(
            template_name='drinks/includes/compare_form.html',
            context={'form': form},
            request=request
        )
    }

    if form.is_valid():
        json_data['form_is_valid'] = True
        years_data = [form_data_dict['year1'], form_data_dict['year2']]
        chart_serries = H.several_years_consumption(years_data)

    if len(chart_serries) == 2:
        template = 'drinks/includes/chart_consumsion_history.html'
        context = {'serries': chart_serries, 'chart_container_name': 'compare_chart'}
        json_data['html'] = render_to_string(template, context, request)
    else:
        json_data['html'] = 'Trūksta duomenų'

    return JsonResponse(json_data)


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        H.context_to_reload(self.request, context)

        context['tab'] = 'index'
        context['all_years'] = len(years())
        context['compare_form'] = render_to_string(
            template_name='drinks/includes/compare_form.html',
            context={'form': forms.DrinkCompareForm()},
            request=self.request
        )

        return context


class Lists(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        context['tab'] = 'data'
        context['data'] = render_to_string(
            'drinks/includes/drinks_list.html',
            {'items': models.Drink.objects.year(year)},
            self.request
        )
        return context


class New(CreateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


class Summary(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = list(models.Drink.objects.summary())
        drink_years = [x['year'] for x in qs]

        context['tab'] = 'history'
        context['drinks_categories'] = drink_years
        context['drinks_data_ml'] = [x['per_day'] for x in qs]
        context['drinks_data_alcohol'] = [x['qty'] * 0.025 for x in qs]
        context['drinks_cnt'] = len(drink_years) - 1.5

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
