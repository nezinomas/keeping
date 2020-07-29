import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, reverse
from django.template.loader import render_to_string

from ..core.lib.date import years
from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models
from .lib.stats import Stats


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.year

        qs = models.Night.objects.sum_by_day(year=year)
        obj = Stats(year=year, data=qs)

        context['chart_weekdays'] = render_to_string(
            'nights/includes/chart_periodicity.html',
            {
                'data': [x['count'] for x in obj.weekdays_stats()],
                'categories': [x[:4] for x in Stats.weekdays()],
                'chart': 'chart_weekdays',
                'chart_title': f'Savaitės dienos, {year} metai',
            },
            self.request
        )

        context['chart_months'] = render_to_string(
            'nights/includes/chart_periodicity.html',
            {
                'data': obj.months_stats(),
                'categories': Stats.months(),
                'chart': 'chart_months',
                'chart_title': f'Mėnesiai, {year} metai'
            },
            self.request
        )

        return context


class Lists(ListMixin):
    model = models.Night


class New(CreateAjaxMixin):
    model = models.Night
    form_class = forms.NightForm


class Update(UpdateAjaxMixin):
    model = models.Night
    form_class = forms.NightForm


@login_required()
def historical_data(request):
    pass


def reload_stats(request):
    pass
