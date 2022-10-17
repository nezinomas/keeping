from typing import Dict, List

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from ..lib.stats import Stats
from ..models import Count, CountType
from .stats import Stats


class CounTypetObjectMixin():
    object = None

    def get_object(self):
        if self.object:
            return

        count_type_slug = self.kwargs.get('slug')

        if count_type_slug:
            try:
                self.object = \
                    CountType.objects \
                    .related() \
                    .get(slug=count_type_slug)
            except CountType.DoesNotExist:
                pass


class ContextMixin():
    render_context = None

    def get_statistic(self):
        year = self.get_year()
        qs_data = self.get_queryset()
        past_last_record = None

        if year:
            try:
                qs_past = \
                    Count.objects \
                    .related() \
                    .filter(date__year__lt=self.get_year(), count_type=self.object) \
                    .latest()

                past_last_record = qs_past.date
            except (Count.DoesNotExist, AttributeError):
                pass

        return Stats(year=year, data=qs_data, past_latest=past_last_record)

    def get_context_data(self, **kwargs):
        statistic = self.get_statistic()

        self.render_context = RenderContext(self.request, statistic)

        context = super().get_context_data(**kwargs)
        context.update({
            'records': statistic.number_of_recods,
        })

        return context


class RenderContext():
    def __init__(self, request: HttpRequest, stats: Stats = None):
        self._request = request
        self._year = request.user.year
        self._stats = stats

    @property
    def calender_data(self):
        return self._stats.chart_calendar()

    def chart_weekdays(self, title: str = None) -> str:
        if not title:
            title = _('Weekdays, %(year)s year') % ({'year': self._year})

        rendered = render_to_string(
            'counts/includes/chart_periodicity.html',
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

    def chart_months(self, title: str = None) -> str:
        if not title:
            title = self._year

        rendered = render_to_string(
            'counts/includes/chart_periodicity.html',
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

    def chart_years(self, title: str = _lazy('Year')) -> str:
        year_totals = self._stats.year_totals()
        rendered = render_to_string(
            'counts/includes/chart_periodicity.html',
            {
                'data': list(year_totals.values()),
                'categories': list(year_totals.keys()),
                'chart': 'chart_years',
                'chart_title': title,
                'chart_column_color': '70, 171, 157',
            },
            self._request
        )

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
        rendered = render_to_string(
            'counts/includes/chart_periodicity.html',
            {
                'data': list(gaps.values()),
                'categories': [f'{x}d' for x in gaps.keys()],
                'chart': 'chart_histogram',
                'chart_title': _('Frequency of gaps, in days'),
                'chart_column_color': '196, 37, 37',
            },
            self._request
        )
        return rendered
