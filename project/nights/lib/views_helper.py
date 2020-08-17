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

    def render_chart_weekdays(self, title):
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

    def render_chart_months(self, title):
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

    def render_chart_years(self, title):
        year_totals = self._stats.year_totals()
        rendered = render_to_string(
            f'{App_name}/includes/chart_periodicity.html',
            {
                'data': list(year_totals.values()),
                'categories': list(year_totals.keys()),
                'chart': 'chart_years',
                'chart_title': 'Metai',
                'chart_column_color': '70, 171, 157',
            },
            self._request
        )
        return rendered

    def render_chart_year(self):
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

    def render_chart_histogram(self):
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

    def render_info_row(self, year: int):
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

    def render_list_data(self):
        rendered = render_to_string(
            f'{App_name}/includes/{App_name}_list.html',
            {
                'items': self._stats.items(),
                **UpdateLinkMixin().get_context_data(),
            },
            self._request
        )
        return rendered

    def context_to_reload(self, year: int):
        context = {
            'tab': 'index',
            'chart_weekdays': self.render_chart_weekdays(f'Savaitės dienos, {year} metai'),
            'chart_months': self.render_chart_months(f'Mėnesiai, {year} metai'),
            'chart_year': self.render_chart_year(),
            'chart_histogram': self.render_chart_histogram(),
            'info_row': self.render_info_row(year),
        }
        return context

    def context_url_names(self):
        context = {
            'app_name': App_name,
            'url_new': f'{App_name}:{App_name}_new',
            'url_index': f'{App_name}:{App_name}_index',
            'url_list': f'{App_name}:{App_name}_list',
            'url_history': f'{App_name}:{App_name}_history',
            'url_reload': f'{App_name}:reload_stats',
        }
        return context
