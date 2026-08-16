import contextlib
import datetime

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from ...core.lib.calendar_grid import CalendarGrid
from ...core.lib.day_stats import Stats
from ...users.models import User
from ..lib.rhythm import GapBin, Rhythm
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
    def span(self) -> str:
        """A chart that pools must caption the years it pooled."""
        years = list(self._stats.totals_by_year())

        if not years:
            return str(self._year)

        return str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"

    def chart_weekdays(self, title: str = None) -> str:
        if not title:
            title = _("Days of week")

        return {
            "data": [x["count"] for x in self._stats.weekdays_stats()],
            "categories": [x[:4] for x in Stats.weekdays()],
            "chart_title": title,
            "subtitle": self.span,
        }

    def chart_months(self, title: str = None) -> str:
        if not title:
            title = _("Months")

        return {
            "data": self._stats.months_stats(),
            "categories": Stats.months(),
            "chart_title": title,
            "subtitle": self.span,
        }

    def chart_years(self, title: str = _lazy("Year")) -> str:
        year_totals = self._stats.totals_by_year()
        return {
            "data": list(year_totals.values()),
            "categories": list(year_totals.keys()),
            "chart_title": title,
            "subtitle": self.span,
        }

    def chart_histogram(self, bins: list[GapBin]) -> dict:
        return {
            "data": [x.count for x in bins],
            "categories": [x.label for x in bins],
            "chart_title": _("Frequency of gaps, in days"),
            "subtitle": self.span,
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
    daily = list(data.sum_by_day)
    latest_past_date = data.past_latest
    stats = Stats(year=year, data=daily, past_latest=latest_past_date)
    srv = IndexService(year, stats)

    return {
        "calendar": CalendarGrid.build(
            year=year,
            daily_data=daily,
            latest_past_date=latest_past_date,
            empty_title=_("No records"),
            low_title=_("No records"),
            high_title=_("Record"),
        ),
    }


def load_periodicity_service(user, count_type: str) -> dict:
    year = user.year
    records = list(Data(user, count_type).items)
    srv = IndexService(year, Stats(data=records))

    return {
        "chart_weekdays": srv.chart_weekdays(),
        "chart_months": srv.chart_months(),
        "chart_histogram": srv.chart_histogram(Rhythm(records).gap_distribution),
    }


def load_history_service(user, count_type: str) -> dict:
    year = user.year
    stats = Stats(data=Data(user, count_type).items)
    srv = IndexService(year, stats)

    return {
        "records": srv.records,
        "chart_years": srv.chart_years(),
    }
