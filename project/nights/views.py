from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, reverse
from django.template.loader import render_to_string

from ..core.lib.date import weeknumber
from ..core.mixins.views import CreateAjaxMixin, IndexMixin, UpdateAjaxMixin
from . import forms, models
from .lib.stats import Stats


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        return context_to_reload(self.request, year, context)


class Lists(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        qs = models.Night.objects.year(year)
        obj = Stats(year=year, data=qs)

        shared_tab_context(self.request, obj, year, context)
        context['tab'] = 'data'
        context['data'] = render_to_string(
            'nights/includes/nights_list.html',
            {
                'items': obj.items(),
            },
            self.request
        )
        return context


class New(CreateAjaxMixin):
    model = models.Night
    form_class = forms.NightForm


class Update(UpdateAjaxMixin):
    model = models.Night
    form_class = forms.NightForm


class History(IndexMixin):
    pass


def reload_stats(request):
    try:
        request.GET['ajax_trigger']
    except KeyError:
        return redirect(reverse('nights:nights_index'))

    return render(
        request=request,
        template_name='nights/includes/reload_stats.html',
        context=context_to_reload(request, request.user.year)
    )


def context_to_reload(request, year, context=None):
    context = context if context else {}

    qs = models.Night.objects.sum_by_day(year=year)
    obj = Stats(year=year, data=qs)

    context['tab'] = 'index'

    shared_tab_context(request, obj, year, context)

    context['chart_weekdays'] = render_to_string(
        'nights/includes/chart_periodicity.html',
        {
            'data': [x['count'] for x in obj.weekdays_stats()],
            'categories': [x[:4] for x in Stats.weekdays()],
            'chart': 'chart_weekdays',
            'chart_title': f'Savaitės dienos, {year} metai',
            'chart_column_color': '70, 171, 157',
        },
        request
    )

    context['chart_months'] = render_to_string(
        'nights/includes/chart_periodicity.html',
        {
            'data': obj.months_stats(),
            'categories': Stats.months(),
            'chart': 'chart_months',
            'chart_title': f'Mėnesiai, {year} metai',
            'chart_column_color': '70, 171, 157',
        },
        request
    )

    context['chart_year'] = render_to_string(
        'nights/includes/chart_month_periodicity.html',
        {
            'month_days': obj.month_days(),
            'month_titles': obj.months(),
            'data': obj.year_stats(),
            'chart_column_color': '113, 149, 198',
        },
        request
    )
    return context

def shared_tab_context(request, obj: Stats, year: int, context):
    week = weeknumber(year)
    total = obj.year_totals()

    context['info_row'] = render_to_string(
        'nights/includes/info_row.html',
        {
            'week': week,
            'total': total,
            'ratio': total / week,
        },
        request
    )
