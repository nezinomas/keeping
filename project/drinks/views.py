import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from ..core.lib.date import years
from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models
from .lib.drinks_stats import DrinkStats
from .lib.views_helper import context_to_reload, several_years_consumption


def reload_stats(request):
    ajax_trigger = request.GET.get('ajax_trigger')
    name = 'drinks/includes/reload_stats.html'

    context = {}

    if ajax_trigger:
        context_to_reload(request, context)

        return render(request, name, context)


@login_required()
def historical_data(request, qty):
    year = request.user.year + 1
    ser = several_years_consumption(range(year - qty, year))

    template = 'drinks/includes/chart_consumsion_history.html'
    context = {'ser': ser, 'chart_container_name': 'history_chart'}
    rendered = render_to_string(template, context, request)

    return JsonResponse({'html': rendered})


@login_required()
def compare(request):
    form_data = request.POST.get('form_data')

    if not form_data:
        return JsonResponse({'error': 'compare Form is broken.'}, status=404)

    try:
        form_data_dict = {}
        form_data_list = json.loads(form_data)

        # flatten list of dictionaries - form_data_list
        for field in form_data_list:
            form_data_dict[field["name"]] = field["value"]

    except Exception:
        return JsonResponse({'error': 'compare Form is broken.'}, status=500)

    json_data = {}
    ser = None
    form = forms.DrinkCompareForm(data=form_data_dict)

    if form.is_valid():
        json_data['form_is_valid'] = True

        years_data = [form_data_dict['year1'], form_data_dict['year2']]
        ser = several_years_consumption(years_data)

    else:
        json_data['form_is_valid'] = False

    if not ser or len(ser) != 2:
        json_data['html'] = 'Trūksta duomenų'
    else:
        template = 'drinks/includes/chart_consumsion_history.html'
        context = {'ser': ser, 'chart_container_name': 'compare_chart'}
        json_data['html'] = render_to_string(template, context, request)

    json_data['html_form'] = render_to_string(
        template_name='drinks/includes/compare_form.html',
        context={'form': form},
        request=request
    )

    return JsonResponse(json_data)


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        qs_target = models.DrinkTarget.objects.year(year)

        context = super().get_context_data(**kwargs)
        context_to_reload(self.request, context)

        context['drinks_list'] = Lists.as_view()(self.request, as_string=True)

        context['target_list'] = render_to_string(
            'drinks/includes/drinks_target_list.html',
            {'items': qs_target},
            self.request)

        context['all_years'] = len(years())

        context['compare_form'] = render_to_string(
            template_name='drinks/includes/compare_form.html',
            context={'form': forms.DrinkCompareForm()},
            request=self.request
        )

        return context


class Lists(ListMixin):
    model = models.Drink


class New(CreateAjaxMixin):
    model = models.Drink
    form_class = forms.DrinkForm


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
