import contextlib
import datetime
from typing import Dict, List

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from ...core.lib.translation import weekday_names
from ...users.models import User
from ..lib.stats import Stats
from ..models import Count
from ..services.model_services import CountModelService


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
            title = _("Weekdays, %(year)s year") % ({"year": self._year})

        return {
            "data": [x["count"] for x in self._stats.weekdays_stats()],
            "categories": [x[:4] for x in Stats.weekdays()],
            "chart_title": title,
            "chart_column_color": "70, 171, 157",
        }

    def chart_months(self, title: str = None) -> str:
        if not title:
            title = self._year

        return {
            "data": self._stats.months_stats(),
            "categories": Stats.months(),
            "chart_title": title,
            "chart_column_color": "70, 171, 157",
        }

    def chart_years(self, title: str = _lazy("Year")) -> str:
        year_totals = self._stats.year_totals()
        return {
            "data": list(year_totals.values()),
            "categories": list(year_totals.keys()),
            "chart_title": title,
            "chart_column_color": "70, 171, 157",
        }

    def chart_calendar(self, data: List[Dict]) -> str:
        return {
            "data": data,
            "categories": [x[0] for x in list(weekday_names().values())],
            "text": {
                "gap": _("Gap"),
                "quantity": _("Quantity"),
            },
        }

    def chart_histogram(self) -> str:
        gaps = self._stats.gaps()
        return {
            "data": list(gaps.values()),
            "categories": [f"{x}d" for x in gaps.keys()],
            "chart_title": _("Frequency of gaps, in days"),
            "chart_column_color": "196, 37, 37",
        }


class Data:
    def __init__(self, user: User, count_type: str):
        self.user = user
        self.year = user.year
        self.count_type: str = count_type

    @property
    def sum_by_day(self) -> list[dict]:
        return CountModelService(self.user).sum_by_day(
            year=self.year, count_type=self.count_type
        )

    @property
    def items(self) -> list[dict]:
        return (
            CountModelService(self.user)
            .items(count_type=self.count_type)
            .values("date", "quantity")
        )

    @property
    def past_latest(self) -> datetime.date:
        past_last_record = None
        with contextlib.suppress(Count.DoesNotExist, AttributeError):
            past_last_record = (
                CountModelService(self.user)
                .objects.filter(
                    date__year__lt=self.year, count_type__slug=self.count_type
                )
                .latest()
                .date
            )
        return past_last_record


def load_index_service(user, count_type: str) -> dict:
    year = user.year
    data = Data(user, count_type)
    stats = Stats(year=year, data=data.sum_by_day, past_latest=data.past_latest)
    srv = IndexService(year, stats)

    # cash calendar data
    calendar_data = srv.calendar_data

    return {
        "chart_calendar_1H": srv.chart_calendar(calendar_data[:6]),
        "chart_calendar_2H": srv.chart_calendar(calendar_data[6:]),
        "chart_weekdays": srv.chart_weekdays(),
        "chart_months": srv.chart_months(),
        "chart_histogram": srv.chart_histogram(),
    }


def load_history_service(user, count_type: str) -> dict:
    year = user.year
    data = Data(user, count_type).items
    stats = Stats(data=data)
    srv = IndexService(year, stats)

    return {
        "records": srv.records,
        "chart_weekdays": srv.chart_weekdays(_("Days of week")),
        "chart_years": srv.chart_years(),
        "chart_histogram": srv.chart_histogram(),
    }
