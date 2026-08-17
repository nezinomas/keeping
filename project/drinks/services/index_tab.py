from dataclasses import dataclass, field
from datetime import date as dt_date
from datetime import datetime

from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils.translation import gettext as _

from ...core.lib import stat_card
from ...core.lib.calendar_grid import CalendarGrid
from ...core.lib.date import ydays, years
from ...core.lib.stat_card import (
    Card,
    ComparisonStatCard,
    EmptyStatCard,
    LevelStatCard,
    StatCard,
)
from ...core.lib.translation import month_names
from ...core.lib.year_boundary import YearBoundary
from ..lib.chart_view_model import ChartViewModel
from ..lib.drink_types import DrinkType
from ..lib.drinks_frequency import FrequencyStats
from ..lib.drinks_options import DrinkConverter
from ..lib.drinks_risk import CALENDAR_LEVELS
from ..lib.drinks_stats import (
    DrinkStats,
    EmptyYearOverYear,
    YearOverYear,
    YearOverYearReading,
)
from ..tabs import DrinkTab
from .consumption_year import ConsumptionYear


@dataclass(frozen=True)
class MonthlyChartViewModel(ChartViewModel):
    categories: list[str]
    data: list[float | None]
    text: dict[str, str]
    target: float | None = None
    avg: float | None = None
    decimals: int = 0


@dataclass(frozen=True)
class DryDaysViewModel:
    date: dt_date | None = None
    delta: int = 0

    @property
    def has_data(self) -> bool:
        return self.date is not None


@dataclass(frozen=True)
class ConversionRowViewModel:
    title: str
    total: float
    per_day: float
    per_week: float
    per_month: float


@dataclass(frozen=True)
class StdAvViewModel:
    items: list[ConversionRowViewModel] = field(default_factory=list)


class IndexTab:
    @classmethod
    def build(cls, user, year: int) -> dict:
        records = ConsumptionYear(user, year)
        target = records.target

        boundary = YearBoundary.for_year(year)

        builder = IndexBuilder(
            converter=records.converter,
            drink_stats=DrinkStats(records.converter, records.monthly),
            previous_stats=DrinkStats(
                records.converter,
                records.previous.daily,
                today=boundary.previous_end_date,
            ),
            frequency_stats=FrequencyStats(
                current_daily=records.daily, past_daily=records.previous.daily
            ),
            target=target.qty,
            target_id=target.target_id,
            latest_past_date=records.last_recorded_date_before,
            latest_current_date=records.last_recorded_date,
        )

        return {
            "all_years": len(years()),
            "chart_quantity": builder.chart_quantity(),
            "chart_consumption": builder.chart_consumption(),
            "tbl_std_av": builder.tbl_std_av(),
            "cards": builder.get_cards(),
            "calendar": CalendarGrid.build(
                year=year,
                daily_data=records.daily_rows,
                latest_past_date=records.last_recorded_date_before,
                unit="Std Av",
                thresholds=CALENDAR_LEVELS,
                value_key="stdav",
                empty_title=_("No drink"),
                low_title=_("No drink"),
                high_title=_("Heavy day"),
            ),
        }


class IndexBuilder:
    def __init__(
        self,
        converter: DrinkConverter,
        drink_stats: DrinkStats,
        previous_stats: DrinkStats | None = None,
        frequency_stats: FrequencyStats | None = None,
        target: float = 0.0,
        target_id: int = 0,
        latest_past_date: dt_date | None = None,
        latest_current_date: dt_date | None = None,
        today: dt_date | None = None,
    ):
        self._target = target
        self._target_id = target_id
        self._latest_past_date = latest_past_date
        self._latest_current_date = latest_current_date
        self._today = today or datetime.now().date()
        self._drink_stats = drink_stats
        self._previous_stats = previous_stats or DrinkStats(converter)
        self._frequency_stats = frequency_stats or FrequencyStats()
        self._converter = converter

    def chart_quantity(self) -> MonthlyChartViewModel:
        return MonthlyChartViewModel(
            categories=list(month_names().values()),
            data=self._drink_stats.monthly.total_quantity,
            text={"quantity": _("Quantity")},
        )

    def chart_consumption(self) -> MonthlyChartViewModel:
        unit = self._converter.display_unit

        return MonthlyChartViewModel(
            categories=list(month_names().values()),
            data=self._drink_stats.monthly.avg_daily_volume,
            target=self._target,
            avg=self._drink_stats.yearly.avg_daily_volume,
            decimals=self._converter.display_decimals,
            text={
                "limit": _("Limit"),
                "alcohol": f"{_('Alcohol consumption per day')}, {unit}",
                "unit": unit,
            },
        )

    def tbl_dry_days(self) -> DryDaysViewModel:
        if latest := self._latest_current_date or self._latest_past_date:
            delta = (self._today - latest).days
            return DryDaysViewModel(date=latest, delta=delta)

        return DryDaysViewModel()

    def get_cards(self) -> list[Card]:
        return [
            self._card_dry_days(),
            self._card_drinking_days(),
            self._card_std_drinks(),
            self._card_avg_per_day(),
            self._card_pure_alcohol(),
            self._card_limit(),
        ]

    @staticmethod
    def _last_year(value: str) -> str:
        return f"{_('Last year')} {value}"

    @staticmethod
    def _arrow_note() -> str:
        return _("The arrow compares with last year, up to the same date.")

    def _against_last_year(
        self, current: float, previous: float
    ) -> YearOverYearReading:
        if not self._previous_stats.yearly.total_quantity:
            return EmptyYearOverYear(current)

        return YearOverYear(current, previous)

    def _card_dry_days(self) -> Card:
        title = _("Days dry")
        dry = self.tbl_dry_days()

        if not dry.has_data:
            return EmptyStatCard(title, _("No data"))

        return StatCard(
            title=title,
            value=str(dry.delta),
            note=dry.date.strftime("%Y-%m-%d"),
        )

    def _card_drinking_days(self) -> Card:
        title = _("Drinking days")
        frequency = self._frequency_stats

        if not frequency.drinking_days:
            return EmptyStatCard(title, _("No data"))

        value = str(frequency.drinking_days)
        share = (
            _("%(share)s%% of the year so far")
            if frequency.is_current_year
            else _("%(share)s%% of the year")
        )
        share = share % {"share": f"{frequency.drinking_day_share * 100:.0f}"}
        definition = _("Calendar days with at least one Drink recorded.")
        comparison = frequency.compare_frequency()

        if not comparison.has_past:
            return StatCard(
                title=title,
                value=value,
                note=share,
                explanation=(share, definition),
            )

        return ComparisonStatCard(
            title,
            improving=comparison.improving,
            value=value,
            note=self._last_year(f"{comparison.previous:.0f}"),
            explanation=(share, definition, self._arrow_note()),
        )

    def _card_std_drinks(self) -> Card:
        title = _("Std drinks")

        if not self._drink_stats.yearly.total_quantity:
            return EmptyStatCard(title, _("No data"))

        stdav = self._drink_stats.yearly.stdav
        value = f"{stdav:.0f}"
        comparison = self._against_last_year(stdav, self._previous_stats.yearly.stdav)

        if not comparison.has_past:
            return StatCard(title=title, value=value, note=_("Std Av this year"))

        return ComparisonStatCard(
            title,
            improving=comparison.improving,
            value=value,
            note=self._last_year(f"{comparison.previous:.0f}"),
            explanation=(self._arrow_note(),),
        )

    def _card_avg_per_day(self) -> Card:
        title = _("Avg per day")

        if not self._drink_stats.yearly.total_quantity:
            return EmptyStatCard(title, _("No data"))

        unit = self._converter.display_unit
        decimals = self._converter.display_decimals

        avg = self._avg_daily(self._drink_stats)
        figure_unit = self._converter.figure_unit
        value = f"{avg:.{decimals}f}"

        comparison = self._against_last_year(avg, self._avg_daily(self._previous_stats))
        baseline = self._last_year(f"{comparison.previous:.{decimals}f}")

        explanation = (f"{unit} {_('per calendar day')}",)

        if comparison.has_past:
            explanation += (self._arrow_note(),)

        if not self._target:
            if not comparison.has_past:
                return StatCard(
                    title=title,
                    value=value,
                    unit=figure_unit,
                    note=_("No limit set"),
                    explanation=explanation,
                )

            return ComparisonStatCard(
                title,
                improving=comparison.improving,
                value=value,
                unit=figure_unit,
                note=baseline,
                explanation=explanation,
            )

        under_limit = avg <= self._target
        diff = f"{abs(self._target - avg):.{decimals}f}"
        direction = _("under the limit") if under_limit else _("over the limit")
        limit_note = f"{diff} {direction}"

        state = stat_card.LOW if under_limit else stat_card.HIGH

        if not comparison.has_past:
            return LevelStatCard(
                title,
                state=state,
                value=value,
                unit=figure_unit,
                note=limit_note,
                explanation=explanation,
            )

        return LevelStatCard(
            title,
            state=state,
            value=value,
            unit=figure_unit,
            note=baseline,
            show_icon=True,
            improving=comparison.improving,
            explanation=explanation,
        )

    def _avg_daily(self, stats: DrinkStats) -> float:
        if self._converter.is_canonical:
            return stats.yearly.avg_daily_stdav

        return stats.yearly.avg_daily_volume

    def _card_pure_alcohol(self) -> Card:
        title = _("Pure alcohol")

        if not self._drink_stats.yearly.total_quantity:
            return EmptyStatCard(title, _("No data"))

        liters = self._drink_stats.yearly.pure_alcohol_liters
        value = f"{liters:.1f}"
        comparison = self._against_last_year(
            liters, self._previous_stats.yearly.pure_alcohol_liters
        )

        if not comparison.has_past:
            return StatCard(title=title, value=value, unit="L", note=_("this year"))

        return ComparisonStatCard(
            title,
            improving=comparison.improving,
            value=value,
            unit="L",
            note=self._last_year(f"{comparison.previous:.1f}"),
            explanation=(self._arrow_note(),),
        )

    def _card_limit(self) -> Card:
        title = _("Daily limit")
        label = _("Goal for the year")

        if not self._target:
            return EmptyStatCard(
                title=title,
                note=_("No limit set"),
                edit_url=DrinkTab.resolve("index").form_url("drinks:target_new"),
                edit_label=label,
            )

        decimals = self._converter.display_decimals

        return StatCard(
            title=title,
            value=f"{self._target:.{decimals}f}",
            unit=self._converter.figure_unit,
            note=_("%(amount)s per year") % {"amount": self._target_a_year()},
            edit_url=reverse("drinks:target_update", kwargs={"pk": self._target_id}),
            edit_label=label,
        )

    def _target_a_year(self) -> str:
        """A daily limit as the year it adds up to, in the unit a total takes."""
        days = ydays(self._drink_stats.year)
        total = self._converter.display_to_total(self._target * days)

        return f"{floatformat(total, 1)} {self._converter.total_unit}"

    def tbl_std_av(self) -> StdAvViewModel:
        return StdAvViewModel(
            items=self._build_conversion_rows(
                self._drink_stats.year, self._drink_stats.yearly.total_quantity
            )
        )

    def _build_conversion_rows(
        self, year: int | None, qty: float
    ) -> list[ConversionRowViewModel]:
        if not qty:
            return []

        day, week, month = self._get_period_counts(year)
        base = (qty, qty / day, qty / week, qty / month)

        return [self._create_conversion_row(t, base) for t in DrinkType]

    def _create_conversion_row(
        self, drink_type: DrinkType, base: tuple[float, ...]
    ) -> ConversionRowViewModel:
        converter = DrinkConverter(drink_type)
        title = drink_type.label

        if not converter.is_canonical:
            one_serving = converter.stdav_to_total(converter.servings_to_stdav(1))
            title = f"{title}, {one_serving:g}{converter.total_unit}"

        total, per_day, per_week, per_month = (
            converter.stdav_to_servings(self._converter.servings_to_stdav(value))
            for value in base
        )

        return ConversionRowViewModel(
            title=title,
            total=total,
            per_day=per_day,
            per_week=per_week,
            per_month=per_month,
        )

    def _get_period_counts(self, year: int | None) -> tuple[int, int, int]:
        boundary = YearBoundary.for_year(year, self._today)

        return (
            boundary.days_elapsed,
            boundary.weeks_elapsed,
            boundary.end_date.month,
        )
