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


def render_chart_months(request, obj, title):
    rendered = render_to_string(
        f'{App_name}/includes/chart_periodicity.html',
        {
            'data': obj.months_stats(),
            'categories': Stats.months(),
            'chart': 'chart_months',
            'chart_title': title,
            'chart_column_color': '70, 171, 157',
        },
        request
    )
    return rendered


def render_chart_years(request, obj, title):
    rendered = render_to_string(
        f'{App_name}/includes/chart_periodicity.html',
        {
            'data': list(obj.values()),
            'categories': list(obj.keys()),
            'chart': 'chart_years',
            'chart_title': 'Metai',
            'chart_column_color': '70, 171, 157',
        },
        request
    )
    return rendered


def render_chart_year(request, obj):
    rendered = render_to_string(
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
    return rendered


def render_chart_histogram(request, obj):
    rendered = render_to_string(
        f'{App_name}/includes/chart_periodicity.html',
        {
            'data': list(obj.values()),
            'categories': [f'{x}d' for x in obj.keys()],
            'chart': 'chart_histogram',
            'chart_title': 'Tarpų dažnis, dienomis',
            'chart_column_color': '196, 37, 37',
        },
        request
    )
    return rendered


def render_info_row(request, obj: Stats, year: int):
    week = weeknumber(year)
    total = obj.year_totals()

    rendered = render_to_string(
        f'{App_name}/includes/info_row.html',
        {
            'week': week,
            'total': total,
            'ratio': total / week,
            'current_gap': obj.current_gap(),
        },
        request
    )
    return rendered


def render_list_data(request, obj):
    rendered = render_to_string(
        f'{App_name}/includes/{App_name}_list.html',
        {
            'items': obj,
            'url_update': f'{App_name}:{App_name}_update',
        },
        request
    )
    return rendered


def context_to_reload(request):
    year = request.user.year
    qs = models.Night.objects.sum_by_day(year=year)
    obj = Stats(year=year, data=qs)

    context = {
        'tab': 'index',
        'chart_weekdays': render_chart_weekdays(request, obj, f'Savaitės dienos, {year} metai'),
        'chart_months': render_chart_months(request, obj, f'Mėnesiai, {year} metai'),
        'chart_year': render_chart_year(request, obj),
        'chart_histogram': render_chart_histogram(request, obj.gaps()),
        'info_row': render_info_row(request, obj, year),
    }
    return context


def context_url_names():
    context = {
        'app_name': App_name,
        'url_new': f'{App_name}:{App_name}_new',
        'url_index': f'{App_name}:{App_name}_index',
        'url_list': f'{App_name}:{App_name}_list',
        'url_history': f'{App_name}:{App_name}_history',
        'url_reload': f'{App_name}:reload_stats',
    }
    return context
