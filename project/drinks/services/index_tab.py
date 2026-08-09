from dataclasses import asdict, dataclass, field
from datetime import date as dt_date
from datetime import datetime

from django.urls import reverse
from django.utils.translation import gettext as _

from ...core.lib import stat_card
from ...core.lib.calendar_grid import CalendarGrid
from ...core.lib.date import ydays, years
from ...core.lib.stat_card import StatCard
from ...core.lib.translation import month_names
from ...core.lib.year_boundary import YearBoundary
from ..lib.drinks_frequency import FrequencyStats
from ..lib.drinks_options import DrinkConverter
from ..lib.drinks_stats import DrinkStats
from .consumption_year import ConsumptionYear


@dataclass(frozen=True)
class ChartViewModel:
    categories: list[str]
    data: list[float | None]
    text: dict[str, str]
    target: float | None = None
    avg: float | None = None
    decimals: int = 0

    @property
    def as_dict(self) -> dict:
        return asdict(self)


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
    """Deep module assembling overview metrics, targets, charts,
    standard unit breakdowns, and calendar grid for the Drinks index tab.
    """

    @classmethod
    def build(cls, user, year: int) -> dict:
        records = ConsumptionYear(user, year)
        target = records.target

        builder = IndexBuilder(
            converter=records.converter,
            drink_stats=DrinkStats(records.converter, records.monthly),
            # counting Drinking days needs the daily rows, which DrinkStats is
            # not given and must not be widened to carry
            frequency_stats=FrequencyStats(
                current_daily=records.daily, past_daily=records.previous.daily
            ),
            target=target.qty,
            target_id=target.target_id,
            # the Drink Target is a daily volume; the card states it a second way,
            # as the pieces of the selected Drink type that volume comes to
            pcs_per_day=(
                target.max_bottles / days
                if target.has_data and (days := ydays(year))
                else 0.0
            ),
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
            ),
        }


class IndexBuilder:
    def __init__(
        self,
        converter: DrinkConverter,
        drink_stats: DrinkStats,
        frequency_stats: FrequencyStats | None = None,
        target: float = 0.0,
        target_id: int = 0,
        pcs_per_day: float = 0.0,
        latest_past_date: dt_date | None = None,
        latest_current_date: dt_date | None = None,
        today: dt_date | None = None,
    ):
        self._target = target
        self._target_id = target_id
        self._pcs_per_day = pcs_per_day
        self._latest_past_date = latest_past_date
        self._latest_current_date = latest_current_date
        self._today = today or datetime.now().date()
        self._drink_stats = drink_stats
        self._frequency_stats = frequency_stats or FrequencyStats()
        self._converter = converter

    def chart_quantity(self) -> ChartViewModel:
        return ChartViewModel(
            categories=list(month_names().values()),
            data=self._drink_stats.monthly.total_quantity,
            text={"quantity": _("Quantity")},
        )

    def chart_consumption(self) -> ChartViewModel:
        unit = self._converter.display_unit

        return ChartViewModel(
            categories=list(month_names().values()),
            data=self._drink_stats.monthly.avg_daily_volume,
            target=self._target,
            avg=self._drink_stats.yearly.avg_daily_volume,
            decimals=self._converter.display_decimals,
            text={
                "limit": _("Limit"),
                # the dropdown names the unit, so this never claims millilitres
                # for an amount that is read as Std Av
                "alcohol": f"{_('Alcohol consumption per day')}, {unit}",
                "unit": unit,
            },
        )

    def tbl_dry_days(self) -> DryDaysViewModel:
        if latest := self._latest_current_date or self._latest_past_date:
            delta = (self._today - latest).days
            return DryDaysViewModel(date=latest, delta=delta)

        return DryDaysViewModel()

    def get_cards(self) -> list[StatCard]:
        # Intensity, the other half of the split, is on the Habits tab: no Std Av
        # figure beside an Avg per day that follows the drink-type dropdown
        return [
            self._card_dry_days(),
            self._card_drinking_days(),
            self._card_std_drinks(),
            self._card_avg_per_day(),
            self._card_pure_alcohol(),
            self._card_limit(),
        ]

    def _card_dry_days(self) -> StatCard:
        title = _("Days dry")
        dry = self.tbl_dry_days()

        if not dry.has_data:
            return StatCard.empty(title, _("No data"))

        return StatCard(
            title=title,
            value=str(dry.delta),
            note=dry.date.strftime("%Y-%m-%d"),
        )

    def _card_drinking_days(self) -> StatCard:
        title = _("Drinking days")
        frequency = self._frequency_stats

        if not frequency.drinking_days:
            return StatCard.empty(title, _("No data"))

        value = str(frequency.drinking_days)
        # a running year's share is of the days elapsed, so the note says so
        # rather than reading as a share of all twelve months
        share = (
            _("%(share)s%% of the year so far")
            if frequency.is_current_year
            else _("%(share)s%% of the year")
        )
        note = share % {"share": f"{frequency.drinking_day_share * 100:.0f}"}
        definition = _("Calendar days with at least one Drink recorded.")
        comparison = frequency.compare_frequency()

        if not comparison.has_past:
            return StatCard(title=title, value=value, note=note, explanation=definition)

        arrow = _("The arrow compares with last year, up to the same date.")

        return StatCard.comparison(
            title,
            improving=comparison.improving,
            value=value,
            note=note,
            explanation=f"{definition} {arrow}",
        )

    def _card_std_drinks(self) -> StatCard:
        title = _("Std drinks")

        if not self._drink_stats.yearly.total_quantity:
            return StatCard.empty(title, _("No data"))

        return StatCard(
            title=title,
            value=f"{self._drink_stats.yearly.stdav:.0f}",
            note=_("Std Av this year"),
        )

    def _card_avg_per_day(self) -> StatCard:
        title = _("Avg per day")

        if not self._drink_stats.yearly.total_quantity:
            return StatCard.empty(title, _("No data"))

        unit = self._converter.display_unit
        decimals = self._converter.display_decimals

        avg = self._drink_stats.yearly.avg_daily_volume
        # the unit the note names is not always the one shown beside the figure:
        # Std Av is read as typed, so the note names it and the figure does not
        figure_unit = unit

        if self._converter.drink_type == "stdav":
            avg = getattr(self._drink_stats.yearly, "avg_daily_stdav", 0.0)
            figure_unit = ""

        value = f"{avg:.{decimals}f}"

        # the Per drinking day card beside this one is Std Av over a different
        # denominator, so this explanation names both of its own
        explanation = f"{unit} {_('per calendar day')}"

        if not self._target:
            return StatCard(
                title=title,
                value=value,
                unit=figure_unit,
                note=_("No limit set"),
                explanation=explanation,
            )

        under_limit = avg <= self._target
        diff = abs(self._target - avg)
        direction = _("under the limit") if under_limit else _("over the limit")

        # a daily average is read against the Drink Target, so it is a level
        return StatCard.level(
            title,
            state=stat_card.LOW if under_limit else stat_card.HIGH,
            value=value,
            unit=figure_unit,
            note=f"{diff:.{decimals}f} {direction}",
            explanation=explanation,
        )

    def _card_pure_alcohol(self) -> StatCard:
        title = _("Pure alcohol")

        if not self._drink_stats.yearly.total_quantity:
            return StatCard.empty(title, _("No data"))

        return StatCard(
            title=title,
            value=f"{self._drink_stats.yearly.pure_alcohol_liters:.1f}",
            unit="L",
            note=_("this year"),
        )

    def _card_limit(self) -> StatCard:
        """The year's Drink Target, and the only way into the form that sets it.

        It was bespoke markup beside the card component until a StatCard could
        carry a pencil, which is what the empty form needs: an unset limit is an
        em dash and a note, and pressing the pencil is what makes it a figure.
        """
        title = _("Daily limit")
        label = _("Goal for the year")

        if not self._target:
            return StatCard(
                title=title,
                note=_("No limit set"),
                state=stat_card.EMPTY,
                edit_url=reverse("drinks:target_new", kwargs={"tab": "index"}),
                edit_label=label,
            )

        unit = self._converter.display_unit
        decimals = self._converter.display_decimals
        # Std Av is read as typed, so the figure carries no unit beside it
        figure_unit = "" if self._converter.drink_type == "stdav" else unit

        return StatCard(
            title=title,
            value=f"{self._target:.{decimals}f}",
            unit=figure_unit,
            note=f"{self._pcs_per_day:.1f} {_('pcs')} / {_('day')}",
            edit_url=reverse("drinks:target_update", kwargs={"pk": self._target_id}),
            edit_label=label,
        )

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

        base_total = qty
        base_per_day = qty / day
        base_per_week = qty / week
        base_per_month = qty / month

        return [
            self._create_conversion_row(
                _("Beer") + ", 0.5L",
                base_total,
                base_per_day,
                base_per_week,
                base_per_month,
                "beer",
            ),
            self._create_conversion_row(
                _("Wine") + ", 0.75L",
                base_total,
                base_per_day,
                base_per_week,
                base_per_month,
                "wine",
            ),
            self._create_conversion_row(
                _("Vodka") + ", 1L",
                base_total,
                base_per_day,
                base_per_week,
                base_per_month,
                "vodka",
            ),
            ConversionRowViewModel(
                title="Std Av",
                total=base_total * self._converter.stdav_per_unit,
                per_day=base_per_day * self._converter.stdav_per_unit,
                per_week=base_per_week * self._converter.stdav_per_unit,
                per_month=base_per_month * self._converter.stdav_per_unit,
            ),
        ]

    def _create_conversion_row(
        self,
        title: str,
        total: float,
        per_day: float,
        per_week: float,
        per_month: float,
        drink_type: str,
    ) -> ConversionRowViewModel:
        return ConversionRowViewModel(
            title=title,
            total=self._converter.convert_qty(total, drink_type),
            per_day=self._converter.convert_qty(per_day, drink_type),
            per_week=self._converter.convert_qty(per_week, drink_type),
            per_month=self._converter.convert_qty(per_month, drink_type),
        )

    def _get_period_counts(self, year: int | None) -> tuple[int, int, int]:
        """Days, weeks and months the year has reached."""
        boundary = YearBoundary.for_year(year, self._today)

        return (
            boundary.days_elapsed,
            boundary.weeks_elapsed,
            boundary.end_date.month,
        )
