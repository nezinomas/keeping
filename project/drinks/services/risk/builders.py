from dataclasses import asdict, dataclass

from django.utils.translation import gettext as _

from ....core.lib.translation import month_names
from ...lib.drinks_risk import (
    HEAVY_DAY_STDAV,
    MONTHLY_HEAVY_HIGH_RISK,
    MONTHLY_HEAVY_LOW_RISK,
    WEEKLY_HIGH_RISK_STDAV,
    WEEKLY_LOW_RISK_STDAV,
    EmptyYearOverYearCount,
    RiskStats,
    YearOverYearCount,
)


@dataclass(frozen=True)
class RiskCardViewModel:
    title: str
    state: str  # "empty", "neutral", "low", "high", "improving", "worsening"
    show_icon: bool
    value: str
    note: str
    explanation: str = ""


@dataclass(frozen=True)
class WeeklyRiskChartViewModel:
    categories: list[str]
    week_ends: list[str]
    data: list[float]
    low_risk: float
    high_risk: float
    text: dict[str, str]

    @property
    def as_dict(self) -> dict:
        """Bridges the gap between strict DTOs and Django's json_script"""
        return asdict(self)


@dataclass(frozen=True)
class MonthlyHeavyDaysChartViewModel:
    categories: list[str]
    data: list[int]
    heavy_threshold: float
    low_risk: float
    high_risk: float
    text: dict[str, str]

    @property
    def as_dict(self) -> dict:
        return asdict(self)


class RiskViewModelBuilder:
    def __init__(self, drink_stats: RiskStats):
        self._stats = drink_stats

    def chart_weekly(self) -> WeeklyRiskChartViewModel:
        series = self._stats.weekly_series()
        return WeeklyRiskChartViewModel(
            categories=[week.label for week in series],
            week_ends=[week.end for week in series],
            data=[week.stdav for week in series],
            low_risk=WEEKLY_LOW_RISK_STDAV,
            high_risk=WEEKLY_HIGH_RISK_STDAV,
            text={
                "title": _("Weekly units with risk bands"),
                "unit": "Std Av",
                "weekly": _("Weekly units"),
                "guideline": _("Low-risk guideline"),
            },
        )

    def chart_heavy_days(self) -> MonthlyHeavyDaysChartViewModel:
        return MonthlyHeavyDaysChartViewModel(
            categories=list(month_names().values()),
            data=self._stats.monthly_heavy_days(),
            heavy_threshold=HEAVY_DAY_STDAV,
            low_risk=MONTHLY_HEAVY_LOW_RISK,
            high_risk=MONTHLY_HEAVY_HIGH_RISK,
            text={
                "title": _("Heavy days per month"),
                "unit": _("Days"),
                "heavy": _("Heavy days"),
                "threshold_label": _("Heavy day"),
                "guideline": _("Low-risk guideline"),
            },
        )

    def get_cards(self) -> list[RiskCardViewModel]:
        return [
            self._build_current_week_card(),
            self._build_worst_week_card(),
            self._build_weeks_over_guideline_card(),
            self._build_heavy_days_card(),
        ]

    def _build_current_week_card(self) -> RiskCardViewModel:
        week = self._stats.current_week()
        return RiskCardViewModel(
            title=_("This week"),
            state=week.state,
            show_icon=False,
            value=f"{week.stdav:.1f}",
            note=f"{_('Low-risk guideline')}: {WEEKLY_LOW_RISK_STDAV:.1f} Std Av",
        )

    def _build_worst_week_card(self) -> RiskCardViewModel:
        week = self._stats.worst_week()
        title = _("Worst week")

        if not week.has_data:
            return RiskCardViewModel(title, "empty", False, "", _("No data"))

        return RiskCardViewModel(
            title=title,
            state=week.state,
            show_icon=False,
            value=f"{week.stdav:.1f}",
            note=f"{week.label} – {week.end}",
        )

    def _build_weeks_over_guideline_card(self) -> RiskCardViewModel:
        definition = _(
            "Weeks whose total exceeds the low-risk guideline of %(threshold)s Std Av."
        ) % {"threshold": f"{WEEKLY_LOW_RISK_STDAV:.1f}"}
        return self._build_comparison_card(
            _("Weeks over guideline"), self._stats.weeks_over_guideline(), definition
        )

    def _build_heavy_days_card(self) -> RiskCardViewModel:
        definition = _("Days with more than %(threshold)s Std Av in a single day.") % {
            "threshold": f"{HEAVY_DAY_STDAV:.0f}"
        }
        return self._build_comparison_card(
            _("Heavy days"), self._stats.heavy_days(), definition
        )

    def _build_comparison_card(
        self,
        title: str,
        stats: YearOverYearCount | EmptyYearOverYearCount,
        definition: str,
    ) -> RiskCardViewModel:
        if not stats.has_past:
            return RiskCardViewModel(
                title=title,
                state="neutral",
                show_icon=False,
                value=str(stats.current),
                note=_("No prior year"),
                explanation=definition,
            )

        state = "improving" if stats.improving else "worsening"
        comparison = _(
            "The two numbers are this year and last year, up to the same date."
        )

        return RiskCardViewModel(
            title=title,
            state=state,
            show_icon=True,
            value=str(stats.current),
            note=f"{stats.current} / {stats.previous}",
            explanation=f"{definition} {comparison}",
        )
