from dataclasses import dataclass
from datetime import date

from django.utils.translation import gettext as _

from ...core.lib.stat_card import (
    HIGH,
    LOW,
    Card,
    ComparisonStatCard,
    EmptyStatCard,
    LevelStatCard,
    StatCard,
)
from ..lib.chart_view_model import ChartViewModel
from ..lib.drinks_trend import (
    EmptyRecentPeriodComparison,
    RecentPeriodComparison,
    TrendStats,
)
from .consumption_year import ConsumptionYear
from .index_tab import DailyLimit, NoDailyLimit


@dataclass(frozen=True)
class TrendChartViewModel(ChartViewModel):
    categories: list[str]
    daily: list[float]
    rolling_7: list[float]
    rolling_30: list[float]
    limit: DailyLimit | NoDailyLimit
    decimals: int
    text: dict[str, str]


@dataclass(frozen=True)
class TrendCumulativeViewModel(ChartViewModel):
    categories: list[str]
    this_year: list[float]
    last_year: list[float]
    target: list[float]
    text: dict[str, str]


class TrendsTab:
    @classmethod
    def build(cls, user, year: int, today: date) -> dict:
        records = ConsumptionYear(user, year, today)
        target = records.target.qty

        stats = TrendStats(
            records.converter,
            current_daily=records.daily,
            past_daily=records.previous.daily,
            target=target,
            year=year,
            today=today,
        )

        limit = NoDailyLimit()
        if target:
            limit = DailyLimit(target)

        builder = TrendsBuilder(drink_stats=stats, limit=limit)

        return {
            "chart_trend": builder.chart_trend(),
            "chart_cumulative": builder.chart_cumulative(),
            "cards": builder.get_cards(),
        }


class TrendsBuilder:
    def __init__(
        self,
        drink_stats: TrendStats,
        limit: DailyLimit | NoDailyLimit = NoDailyLimit(),
    ):
        self._stats = drink_stats
        self._limit = limit

    def _rounded(self, values: list[float]) -> list[float]:
        """Round to the precision the selected unit is read at."""
        return [round(v, self._stats.decimals) for v in values]

    def chart_trend(self) -> TrendChartViewModel:
        return TrendChartViewModel(
            categories=self._stats.date_labels,
            daily=self._rounded(self._stats.daily_volume),
            rolling_7=self._rounded(self._stats.calculate_rolling_average(7)),
            rolling_30=self._rounded(self._stats.calculate_rolling_average(30)),
            limit=self._limit,
            decimals=self._stats.decimals,
            text={
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
                "unit": self._stats.total_unit,
                "this_year": _("This year"),
                "last_year": _("Last year"),
                "target": _("Target pace"),
            },
        )

    def get_cards(self) -> list[Card]:
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
    ) -> Card:
        if not stats.has_data:
            return EmptyStatCard(title, _("No data"))

        current = self._stats.as_total(stats.current_period_average)
        previous = self._stats.as_total(stats.previous_period_average)

        # with no period to compare against there is no percentage to show, so
        # the card falls back to the level itself — and to no unit with it
        value = f"{current:.1f}"
        unit = ""

        if stats.previous_period_average:
            value = f"{stats.percentage_change:.1f}"
            unit = "%"

        return ComparisonStatCard(
            title,
            improving=stats.improving,
            value=value,
            unit=unit,
            note=f"{current:.1f} / {previous:.1f} {self._stats.total_unit}",
        )

    def _build_ytd_card(self) -> Card:
        stats = self._stats.compare_year_to_date()
        title = _("This year vs last")
        # a centred card has no room for "to date" in the title, so the
        # explanation the card already carries says it instead
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

        return ComparisonStatCard(
            title,
            improving=stats.improving,
            value=f"{stats.percentage_change:.1f}",
            unit="%",
            note=f"{current:.1f} / {previous:.1f} {unit}",
            # the note is two figures with nothing naming them, and Risk already
            # owns that sentence for a note of the same shape
            explanation=(
                _("The two numbers are this year and last year, up to the same date."),
                to_date,
            ),
        )

    def _build_projection_card(self) -> Card:
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
        return LevelStatCard(
            title,
            state=HIGH if stats.over else LOW,
            value=f"{stats.projected_total:.1f}",
            unit=unit,
            note=(
                f"{_('Limit')}: {stats.target_total:.1f} {unit} / "
                f"{stats.percentage_difference:.1f}%"
            ),
        )
