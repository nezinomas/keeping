from dataclasses import asdict, dataclass

from django.utils.translation import gettext as _

from ...lib.drinks_trend import (
    EmptyRecentPeriodComparison,
    RecentPeriodComparison,
    TrendStats,
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
class TrendCumulativeViewModel:
    categories: list[str]
    this_year: list[float]
    last_year: list[float]
    target: list[float]
    text: dict[str, str]

    @property
    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TrendCardViewModel:
    title: str
    state: str  # "empty", "neutral", "improving", "worsening"
    show_icon: bool
    value: str
    note: str


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

    def chart_cumulative(self) -> TrendCumulativeViewModel:
        return TrendCumulativeViewModel(
            categories=self._stats.cumulative_categories,
            this_year=[round(v) for v in self._stats.cumulative_current_year_ml],
            last_year=[round(v) for v in self._stats.cumulative_past_year_ml],
            target=[round(v) for v in self._stats.cumulative_target_ml],
            text={
                "this_year": _("This year"),
                "last_year": _("Last year"),
                "target": _("Target pace"),
            },
        )

    def get_cards(self) -> list[TrendCardViewModel]:
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
    ) -> TrendCardViewModel:
        if not stats.has_data:
            return TrendCardViewModel(
                title=title,
                state="empty",
                show_icon=False,
                value="",
                note=_("No data"),
            )

        state = "improving" if stats.improving else "worsening"

        value = (
            f"{stats.percentage_change:.1f}%"
            if stats.previous_period_average
            else f"{stats.current_period_average:.1f}"
        )

        note = (
            f"{stats.current_period_average:.1f} / "
            f"{stats.previous_period_average:.1f} Std Av"
        )

        return TrendCardViewModel(
            title=title,
            state=state,
            show_icon=True,
            value=value,
            note=note,
        )

    def _build_ytd_card(self) -> TrendCardViewModel:
        stats = self._stats.compare_year_to_date()
        title = _("This year vs last (to date)")

        if not stats.has_past:
            return TrendCardViewModel(
                title=title,
                state="neutral",
                show_icon=False,
                value=f"{stats.current_year_average:.1f}",
                note=f"Std Av &middot; {_('No prior year')}",
            )

        state = "improving" if stats.improving else "worsening"

        return TrendCardViewModel(
            title=title,
            state=state,
            show_icon=True,
            value=f"{stats.percentage_change:.1f}%",
            note=(
                f"{stats.current_year_average:.1f} / "
                f"{stats.previous_year_average:.1f} Std Av"
            ),
        )

    def _build_projection_card(self) -> TrendCardViewModel:
        stats = self._stats.calculate_projection()
        title = _("Year-end forecast")

        if not stats.has_target:
            return TrendCardViewModel(
                title=title,
                state="neutral",
                show_icon=False,
                value=f"{stats.projected_volume_liters:.1f} L",
                note=_("No limit set"),
            )

        state = "worsening" if stats.over else "improving"

        return TrendCardViewModel(
            title=title,
            state=state,
            show_icon=False,
            value=f"{stats.projected_volume_liters:.1f} L",
            note=(
                f"{_('Limit')}: {stats.target_volume_liters:.1f} L &middot; "
                f"{stats.percentage_difference:.1f}%"
            ),
        )
