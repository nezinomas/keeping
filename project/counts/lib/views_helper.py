from typing import Dict, List

from django.http import HttpRequest
from django.template.loader import render_to_string

from ...core.lib.date import weeknumber
from ..apps import App_name
from .stats import Stats


class UpdateLinkMixin():
    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
        except AttributeError:
            context = {}

        context.update({'url_update': f'{App_name}:{App_name}_update'})
        return context


class RenderContext():
    def __init__(self, request: HttpRequest, stats: Stats = None):
        self._request = request
        self._stats = stats

    def chart_weekdays(self, title: str) -> str:
        rendered = render_to_string(
            f'{App_name}/includes/chart_periodicity.html',
            {
                'data': [x['count'] for x in self._stats.weekdays_stats()],
                'categories': [x[:4] for x in Stats.weekdays()],
                'chart': 'chart_weekdays',
                'chart_title': title,
                'chart_column_color': '70, 171, 157',
            },
            self._request
        )
        return rendered

    def chart_months(self, title: str) -> str:
        rendered = render_to_string(
            f'{App_name}/includes/chart_periodicity.html',
            {
                'data': self._stats.months_stats(),
                'categories': Stats.months(),
                'chart': 'chart_months',
                'chart_title': title,
                'chart_column_color': '70, 171, 157',
            },
            self._request
        )
        return rendered

    def chart_years(self, title: str = 'Metai') -> str:
        year_totals = self._stats.year_totals()
        rendered = render_to_string(
            f'{App_name}/includes/chart_periodicity.html',
            {
                'data': list(year_totals.values()),
                'categories': list(year_totals.keys()),
                'chart': 'chart_years',
                'chart_title': title,
                'chart_column_color': '70, 171, 157',
            },
            self._request
        )
        return rendered

    def chart_year(self) -> str:
        rendered = render_to_string(
            f'{App_name}/includes/chart_month_periodicity.html',
            {
                'month_days': self._stats.month_days(),
                'month_titles': self._stats.months(),
                'data': self._stats.year_stats(),
                'chart_column_color': '113, 149, 198',
                'alternative_bg': [3, 4, 5, 9, 10, 11],
                'chart_template': f'{App_name}/includes/chart_month.html'
            },
            self._request
        )
        return rendered

    def chart_calendar(self, data: List[Dict], chart_id='F') -> str:

        rendered = render_to_string(
            f'{App_name}/includes/chart_calendar.html',
            {
                'data': data,
                'id': chart_id,
            },
            self._request
        )
        return rendered

    def chart_histogram(self) -> str:
        gaps = self._stats.gaps()
        rendered = render_to_string(
            f'{App_name}/includes/chart_periodicity.html',
            {
                'data': list(gaps.values()),
                'categories': [f'{x}d' for x in gaps.keys()],
                'chart': 'chart_histogram',
                'chart_title': 'Tarpų dažnis, dienomis',
                'chart_column_color': '196, 37, 37',
            },
            self._request
        )
        return rendered

    def info_row(self, year: int) -> str:
        week = weeknumber(year)
        total = self._stats.year_totals()

        rendered = render_to_string(
            f'{App_name}/includes/info_row.html',
            {
                'week': week,
                'total': total,
                'ratio': total / week,
                'current_gap': self._stats.current_gap(),
            },
            self._request
        )
        return rendered

    def list_data(self) -> str:
        rendered = render_to_string(
            f'{App_name}/includes/{App_name}_list.html',
            {
                'items': self._stats.items(),
                **UpdateLinkMixin().get_context_data(),
            },
            self._request
        )
        return rendered

    def context_to_reload(self, year: int) -> Dict[str, str]:
        calendar_data = self._stats.chart_calendar()

        context = {
            'tab': 'index',
            'chart_calendar_1H': self.chart_calendar(calendar_data[0:6], '1H'),
            'chart_calendar_2H': self.chart_calendar(calendar_data[6:], '2H'),
            'chart_weekdays': self.chart_weekdays(f'Savaitės dienos, {year} metai'),
            'chart_months': self.chart_months(f'Mėnesiai, {year} metai'),
            'chart_year': self.chart_year(),
            'chart_histogram': self.chart_histogram(),
            'info_row': self.info_row(year),
        }
        return context

    def context_url_names(self) -> Dict[str, str]:
        context = {
            'app_name': App_name,
            'url_new': f'{App_name}:{App_name}_new',
            'url_index': f'{App_name}:{App_name}_index',
            'url_list': f'{App_name}:{App_name}_list',
            'url_history': f'{App_name}:{App_name}_history',
            'url_reload': f'{App_name}:reload_stats',
        }
        return context
