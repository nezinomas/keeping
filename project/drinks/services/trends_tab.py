from dataclasses import asdict, dataclass

from django.utils.translation import gettext as _

from ..lib.drinks_trend import (
    EmptyRecentPeriodComparison,
    RecentPeriodComparison,
    TrendStats,
)
from . import stat_card
from .consumption_year import ConsumptionYear
from .stat_card import StatCard


@dataclass(frozen=True)
class TrendChartViewModel:
    categories: list[str]
    rolling_7: list[float]
    rolling_30: list[float]
    target: float
    text: dict[str, str]

    @property
    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TrendCumulativeViewModel:
    categories: list[str]
    this_year: list[float]
    last_year: list[float]
    target: list[float]
    text: dict[str, str]

    @property
    def as_dict(self) -> dict:
        return asdict(self)


class TrendsTab:
    """Deep module calculating multi-year drinking trends, cumulative
    consumption projections, and trend direction cards.
    """

    @classmethod
    def build(cls, user, year: int) -> dict:
        records = ConsumptionYear(user, year)
        target = records.target.qty

        stats = TrendStats(
            records.converter,
            current_daily=records.daily,
            past_daily=records.previous.daily,
            target=target,
        )

        builder = TrendsBuilder(drink_stats=stats, target=target)

        return {
            "chart_trend": builder.chart_trend(),
            "chart_cumulative": builder.chart_cumulative(),
            "cards": builder.get_cards(),
        }


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
                "title": _("Rolling average"),
                "unit": "ml",
                "r7": _("7-day average"),
                "r30": _("30-day average"),
                "limit": _("Limit"),
            },
        )

    def chart_cumulative(self) -> TrendCumulativeViewModel:
        return TrendCumulativeViewModel(
            categories=self._stats.cumulative_categories,
            this_year=[
                round(v / 1000, 1) for v in self._stats.cumulative_current_year_ml
            ],
            last_year=[round(v / 1000, 1) for v in self._stats.cumulative_past_year_ml],
            target=[round(v / 1000, 1) for v in self._stats.cumulative_target_ml],
            text={
                "title": _("Cumulative (year over year)"),
                "unit": "L",
                "this_year": _("This year"),
                "last_year": _("Last year"),
                "target": _("Target pace"),
            },
        )

    def get_cards(self) -> list[StatCard]:
        return [
            self._build_period_card(
                _("Trend (2 weeks)"), self._stats.compare_recent_period(14)
            ),
            self._build_period_card(
                _("Trend (month)"), self._stats.compare_recent_period(30)
            ),
            self._build_period_card(
                _("Trend (90 days)"), self._stats.compare_recent_period(90)
            ),
            self._build_ytd_card(),
            self._build_projection_card(),
        ]

    def _build_period_card(
        self, title: str, stats: RecentPeriodComparison | EmptyRecentPeriodComparison
    ) -> StatCard:
        if not stats.has_data:
            return StatCard.empty(title, _("No data"))

        value = (
            f"{stats.percentage_change:.1f}%"
            if stats.previous_period_average
            else f"{stats.current_period_average:.1f}"
        )

        return StatCard.comparison(
            title,
            improving=stats.improving,
            value=value,
            note=(
                f"{stats.current_period_average:.1f} / "
                f"{stats.previous_period_average:.1f} Std Av"
            ),
        )

    def _build_ytd_card(self) -> StatCard:
        stats = self._stats.compare_year_to_date()
        title = _("This year vs last (to date)")

        if not stats.has_past:
            return StatCard(
                title=title,
                value=f"{stats.current_year_average:.1f}",
                note=f"Std Av · {_('No prior year')}",
            )

        return StatCard.comparison(
            title,
            improving=stats.improving,
            value=f"{stats.percentage_change:.1f}%",
            note=(
                f"{stats.current_year_average:.1f} / "
                f"{stats.previous_year_average:.1f} Std Av"
            ),
        )

    def _build_projection_card(self) -> StatCard:
        stats = self._stats.calculate_projection()
        title = _("Year-end forecast")

        if not stats.has_target:
            return StatCard(
                title=title,
                value=f"{stats.projected_volume_liters:.1f} L",
                note=_("No limit set"),
            )

        # a forecast is read against the Drink Target, so it is a level, not a
        # like-for-like comparison against a past period
        return StatCard.level(
            title,
            state=stat_card.HIGH if stats.over else stat_card.LOW,
            value=f"{stats.projected_volume_liters:.1f} L",
            note=(
                f"{_('Limit')}: {stats.target_volume_liters:.1f} L · "
                f"{stats.percentage_difference:.1f}%"
            ),
        )
