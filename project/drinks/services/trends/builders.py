from dataclasses import asdict, dataclass

from django.utils.translation import gettext as _

from ...lib.drinks_trend import (
    EmptyRecentPeriodComparison,
    EmptyYearEndProjection,
    EmptyYearToDateComparison,
    RecentPeriodComparison,
    TrendStats,
    YearEndProjection,
    YearToDateComparison,
)


@dataclass(frozen=True)
class TrendChartViewModel:
    categories: list[str]
    rolling_7: list[float]
    rolling_30: list[float]
    target: float
    text: dict[str, str]

    @property
    def as_dict(self) -> dict:
        """Bridges the gap between strict DTOs and Django's json_script"""
        return asdict(self)


@dataclass(frozen=True)
class TrendItemViewModel:
    title: str
    stats: RecentPeriodComparison | EmptyRecentPeriodComparison


class TrendsBuilder:
    def __init__(self, drink_stats: TrendStats, target: float = 0.0):
        self._stats = drink_stats
        self._target = target

    def chart_trend(self) -> TrendChartViewModel:
        return TrendChartViewModel(
            categories=self._stats.date_labels,
            rolling_7=[round(v) for v in self._stats.calculate_rolling_average(7)],
            rolling_30=[round(v) for v in self._stats.calculate_rolling_average(30)],
            target=self._target,
            text={
                "r7": _("7-day average"),
                "r30": _("30-day average"),
                "limit": _("Limit"),
            },
        )

    def trend_items(self) -> list[TrendItemViewModel]:
        return [
            TrendItemViewModel(
                _("Trend (2 weeks)"), self._stats.compare_recent_period(14)
            ),
            TrendItemViewModel(
                _("Trend (month)"), self._stats.compare_recent_period(30)
            ),
            TrendItemViewModel(
                _("Trend (90 days)"), self._stats.compare_recent_period(90)
            ),
        ]

    def trend_ytd(self) -> YearToDateComparison | EmptyYearToDateComparison:
        return self._stats.compare_year_to_date()

    def trend_projection(self) -> YearEndProjection | EmptyYearEndProjection:
        return self._stats.calculate_projection()
