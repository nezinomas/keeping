from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from ..core.lib.date import years
from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models
from .lib.drinks_stats import DrinkStats
from .lib.views_helper import context_to_reload


def reload_stats(request):
    ajax_trigger = request.GET.get('ajax_trigger')
    name = 'drinks/includes/reload_stats.html'

    context = {}

    if ajax_trigger:
        context_to_reload(request, context)

        return render(request, name, context)

@login_required()
def historical_data(request, qty):
    ser = []
    year = request.user.year + 1
    for y in range (year - qty, year):
        qs_drinks = models.Drink.objects.sum_by_month(y)
        data = DrinkStats(qs_drinks).consumption

        if not any(data):
            continue

        d = {
            'name': y,
            'data': data
        }
        ser.append(d)

    template = 'drinks/includes/chart_consumsion_history.html'
    context = {'ser': ser}
    rendered = render_to_string(template, context, request)

    return JsonResponse({'html': rendered})


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        qs_target = models.DrinkTarget.objects.year(year)

        context = super().get_context_data(**kwargs)
        context_to_reload(self.request, context)

        context['drinks_list'] = Lists.as_view()(
            self.request, as_string=True)

        context['target_list'] = render_to_string(
            'drinks/includes/drinks_target_list.html',
            {'items': qs_target},
            self.request)

        context['all_years'] = len(years())

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
