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
    daily: list[float]
    rolling_7: list[float]
    rolling_30: list[float]
    target: float
    decimals: int
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
            year=year,
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

    def _rounded(self, values: list[float]) -> list[float]:
        """Round to the precision the selected unit is read at."""
        return [round(v, self._stats.decimals) for v in values]

    def chart_trend(self) -> TrendChartViewModel:
        return TrendChartViewModel(
            categories=self._stats.date_labels,
            daily=self._rounded(self._stats.daily_volume),
            rolling_7=self._rounded(self._stats.calculate_rolling_average(7)),
            rolling_30=self._rounded(self._stats.calculate_rolling_average(30)),
            target=self._target,
            decimals=self._stats.decimals,
            text={
                "title": _("Rolling average"),
                # the dropdown decides the unit, so the axes and the tooltip
                # never claim ml for an amount read as Std Av
                "unit": self._stats.unit,
                "daily": _("Per day"),
                "r7": _("7-day average"),
                "r30": _("30-day average"),
                "limit": _("Limit"),
            },
        )

    def chart_cumulative(self) -> TrendCumulativeViewModel:
        return TrendCumulativeViewModel(
            categories=self._stats.cumulative_categories,
            this_year=[round(v, 1) for v in self._stats.cumulative_current_year],
            last_year=[round(v, 1) for v in self._stats.cumulative_past_year],
            target=[round(v, 1) for v in self._stats.cumulative_target],
            text={
                "title": _("Cumulative (year over year)"),
                "unit": self._stats.total_unit,
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

        current = self._stats.as_total(stats.current_period_average)
        previous = self._stats.as_total(stats.previous_period_average)

        # with no period to compare against there is no percentage to show, so
        # the card falls back to the level itself — and to no unit with it
        value = f"{current:.1f}"
        unit = ""

        if stats.previous_period_average:
            value = f"{stats.percentage_change:.1f}"
            unit = "%"

        return StatCard.comparison(
            title,
            improving=stats.improving,
            value=value,
            unit=unit,
            note=f"{current:.1f} / {previous:.1f} {self._stats.total_unit}",
        )

    def _build_ytd_card(self) -> StatCard:
        stats = self._stats.compare_year_to_date()
        title = _("This year vs last")
        # "to date" qualifies the reading rather than naming the metric, and a
        # centred card has no room for a title that long — the explanation the
        # card already carries says it instead
        to_date = _("The arrow compares with last year, up to the same date.")

        unit = self._stats.total_unit
        current = self._stats.as_total(stats.current_year_average)
        previous = self._stats.as_total(stats.previous_year_average)

        if not stats.has_past:
            return StatCard(
                title=title,
                value=f"{current:.1f}",
                note=f"{unit} / {_('No prior year')}",
            )

        return StatCard.comparison(
            title,
            improving=stats.improving,
            value=f"{stats.percentage_change:.1f}",
            unit="%",
            note=f"{current:.1f} / {previous:.1f} {unit}",
            explanation=to_date,
        )

    def _build_projection_card(self) -> StatCard:
        stats = self._stats.calculate_projection()
        title = _("Year-end forecast")
        unit = self._stats.total_unit

        if not stats.has_target:
            return StatCard(
                title=title,
                value=f"{stats.projected_total:.1f}",
                unit=unit,
                note=_("No limit set"),
            )

        # a forecast is read against the Drink Target, so it is a level, not a
        # like-for-like comparison against a past period
        return StatCard.level(
            title,
            state=stat_card.HIGH if stats.over else stat_card.LOW,
            value=f"{stats.projected_total:.1f}",
            unit=unit,
            note=(
                f"{_('Limit')}: {stats.target_total:.1f} {unit} / "
                f"{stats.percentage_difference:.1f}%"
            ),
        )
