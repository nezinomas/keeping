from typing import Dict, List

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from ...core.lib.translation import weekday_names
from ..lib.stats import Stats


class IndexService:
    def __init__(self, year: int, stats: Stats = None):
        self._year = year
        self._stats = stats

    @property
    def records(self):
        return self._stats.number_of_records

    @property
    def calendar_data(self):
        return self._stats.chart_calendar()

    def chart_weekdays(self, title: str = None) -> str:
        if not title:
            title = _('Weekdays, %(year)s year') % ({'year': self._year})

        return {
            'data': [x['count'] for x in self._stats.weekdays_stats()],
            'categories': [x[:4] for x in Stats.weekdays()],
            'chart_title': title,
            'chart_column_color': '70, 171, 157',
        }

    def chart_months(self, title: str = None) -> str:
        if not title:
            title = self._year

        return {
            'data': self._stats.months_stats(),
            'categories': Stats.months(),
            'chart_title': title,
            'chart_column_color': '70, 171, 157',
        }

    def chart_years(self, title: str = _lazy('Year')) -> str:
        year_totals = self._stats.year_totals()
        return {
            'data': list(year_totals.values()),
            'categories': list(year_totals.keys()),
            'chart_title': title,
            'chart_column_color': '70, 171, 157',
        }

    def chart_calendar(self, data: List[Dict]) -> str:
        return {
            'data': data,
            'categories': [x[0] for x in list(weekday_names().values())],
            'text': {
                'gap': _('Gap'),
                'quantity': _('Quantity'),
            }
        }

    def chart_histogram(self) -> str:
        gaps = self._stats.gaps()
        return {
            'data': list(gaps.values()),
            'categories': [f'{x}d' for x in gaps.keys()],
            'chart_title': _('Frequency of gaps, in days'),
            'chart_column_color': '196, 37, 37',
        }