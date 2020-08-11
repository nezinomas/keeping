from django.template.loader import render_to_string

from ...core.lib.date import weeknumber
from .. import models
from ..apps import App_name
from .stats import Stats


def render_chart_weekdays(request, obj, title):
    rendered = render_to_string(
        f'{App_name}/includes/chart_periodicity.html',
        {
            'data': [x['count'] for x in obj.weekdays_stats()],
            'categories': [x[:4] for x in Stats.weekdays()],
            'chart': 'chart_weekdays',
            'chart_title': title,
            'chart_column_color': '70, 171, 157',
        },
        request
    )
    return rendered


def context_to_reload(request, year, context=None):
    context = context if context else {}

    qs = models.Night.objects.sum_by_day(year=year)
    obj = Stats(year=year, data=qs)

    context['tab'] = 'index'

    context_info_row(request, obj, year, context)

    context.update({
        'tab': 'index',
        'chart_weekdays': render_chart_weekdays(request, obj, f'Savaitės dienos, {year} metai')
    })


    context['chart_months'] = render_to_string(
        f'{App_name}/includes/chart_periodicity.html',
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
        f'{App_name}/includes/chart_month_periodicity.html',
        {
            'month_days': obj.month_days(),
            'month_titles': obj.months(),
            'data': obj.year_stats(),
            'chart_column_color': '113, 149, 198',
            'alternative_bg': [3, 4, 5, 9, 10, 11],
            'chart_template': f'{App_name}/includes/chart_month.html'
        },
        request
    )

    gaps = obj.gaps()
    context['chart_histogram'] = render_to_string(
        f'{App_name}/includes/chart_periodicity.html',
        {
            'data': list(gaps.values()),
            'categories': [f'{x}d' for x in gaps.keys()],
            'chart': 'chart_histogram',
            'chart_title': 'Tarpų dažnis, dienomis',
            'chart_column_color': '196, 37, 37',
        },
        request
    )

    return context


def context_info_row(request, obj: Stats, year: int, context):
    week = weeknumber(year)
    total = obj.year_totals()

    context['info_row'] = render_to_string(
        f'{App_name}/includes/info_row.html',
        {
            'week': week,
            'total': total,
            'ratio': total / week,
            'current_gap': obj.current_gap(),
        },
        request
    )


def context_url_names(context):
    context['app_name'] = App_name
    context['url_new'] = f'{App_name}:{App_name}_new'
    context['url_index'] = f'{App_name}:{App_name}_index'
    context['url_list'] = f'{App_name}:{App_name}_list'
    context['url_history'] = f'{App_name}:{App_name}_history'
    context['url_reload'] = f'{App_name}:reload_stats'
