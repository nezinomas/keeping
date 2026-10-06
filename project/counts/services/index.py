from django.utils.dates import WEEKDAYS_ABBR
from django.utils.translation import gettext as _

from ...core.lib.calendar_grid import CalendarGrid
from ...core.lib.day_stats import Stats
from ...core.lib.translation import month_abbr
from ..lib.rhythm import GapBin
from .counter_life import CounterLife
from .model_services import CountModelService


class IndexService:
    def __init__(self, stats: Stats):
        self._stats = stats

    def chart_weekdays(self) -> dict:
        return {
            "data": [x["count"] for x in self._stats.weekdays_stats()],
            "categories": [str(WEEKDAYS_ABBR[day]) for day in range(7)],
        }

    def chart_months(self) -> dict:
        return {
            "data": self._stats.months_stats(),
            "categories": [month_abbr(month) for month in range(1, 13)],
        }

    def chart_years(self) -> dict:
        year_totals = self._stats.totals_by_year()

        return {
            "data": list(year_totals.values()),
            "categories": list(year_totals.keys()),
        }

    def chart_histogram(self, bins: list[GapBin]) -> dict:
        return {
            "data": [x.count for x in bins],
            "categories": [x.label for x in bins],
        }


def load_index_service(life: CounterLife) -> dict:
    daily = list(
        CountModelService(life.user).sum_by_day(
            year=life.boundary.year, count_type=life.count_type
        )
    )

    return {
        "calendar": CalendarGrid.build(
            life.boundary,
            daily_data=daily,
            latest_past_date=life.past_latest,
            empty_title=_("No records"),
            low_title=_("No records"),
            high_title=_("Record"),
        ),
    }


def load_periodicity_service(life: CounterLife) -> dict:
    srv = IndexService(Stats(data=life.records))

    return {
        "span": life.span,
        "chart_weekdays": srv.chart_weekdays(),
        "chart_months": srv.chart_months(),
        "chart_histogram": srv.chart_histogram(life.rhythm.gap_distribution),
    }


def load_history_service(life: CounterLife) -> dict:
    srv = IndexService(Stats(data=life.records))

    return {
        "records": len(life.records),
        "span": life.span,
        "chart_years": srv.chart_years(),
    }
