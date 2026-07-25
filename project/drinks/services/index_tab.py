from dataclasses import asdict, dataclass, field
from datetime import date as dt_date
from datetime import datetime

from django.utils.translation import gettext as _

from ...core.lib.calendar_grid import CalendarGrid
from ...core.lib.date import ydays, years
from ...core.lib.translation import month_names
from ..lib.drinks_options import DrinkConverter
from ..lib.drinks_stats import DrinkStats
from .consumption_year import ConsumptionYear


@dataclass(frozen=True)
class ChartViewModel:
    categories: list[str]
    data: list[float]
    text: dict[str, str]
    target: float | None = None
    avg: float | None = None

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
class AlcoholViewModel:
    liters: float


@dataclass(frozen=True)
class IndexCardViewModel:
    title: str
    value: str
    note: str
    state: str = "neutral"  # "neutral" | "positive" | "negative" | "empty"


@dataclass(frozen=True)
class LimitCardViewModel:
    has_data: bool = False
    ml: float = 0.0
    pcs: float = 0.0
    target_id: int = 0


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
            target=target.qty,
            latest_past_date=records.last_recorded_date_before,
            latest_current_date=records.last_recorded_date,
        )

        limit = LimitCardViewModel(
            has_data=target.has_data,
            ml=target.qty,
            pcs=target.max_bottles,
            target_id=target.target_id,
        )

        return {
            "all_years": len(years()),
            "chart_quantity": builder.chart_quantity(),
            "chart_consumption": builder.chart_consumption(),
            "tbl_std_av": builder.tbl_std_av(),
            "cards": builder.get_cards(),
            "limit": limit,
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
        target: float = 0.0,
        latest_past_date: dt_date | None = None,
        latest_current_date: dt_date | None = None,
        today: dt_date | None = None,
    ):
        self._target = target
        self._latest_past_date = latest_past_date
        self._latest_current_date = latest_current_date
        self._today = today or datetime.now().date()
        self._drink_stats = drink_stats
        self._converter = converter

    def chart_quantity(self) -> ChartViewModel:
        return ChartViewModel(
            categories=list(month_names().values()),
            data=self._drink_stats.monthly.total_quantity,
            text={"quantity": _("Quantity")},
        )

    def chart_consumption(self) -> ChartViewModel:
        return ChartViewModel(
            categories=list(month_names().values()),
            data=self._drink_stats.monthly.avg_daily_volume_ml,
            target=self._target,
            avg=self._drink_stats.yearly.avg_daily_volume_ml,
            text={
                "limit": _("Limit"),
                "alcohol": _("Alcohol consumption per day, milliliters"),
            },
        )

    def tbl_dry_days(self) -> DryDaysViewModel:
        if latest := self._latest_current_date or self._latest_past_date:
            delta = (self._today - latest).days
            return DryDaysViewModel(date=latest, delta=delta)

        return DryDaysViewModel()

    def tbl_alcohol(self) -> AlcoholViewModel:
        stdav = self._drink_stats.yearly.total_quantity / self._converter.ratio
        return AlcoholViewModel(liters=self._converter.stdav_to_alcohol(stdav))

    def get_cards(self) -> list[IndexCardViewModel]:
        return [
            self._card_dry_days(),
            self._card_std_drinks(),
            self._card_avg_per_day(),
            self._card_pure_alcohol(),
        ]

    def _card_dry_days(self) -> IndexCardViewModel:
        title = _("Days dry")
        dry = self.tbl_dry_days()

        if not dry.has_data:
            return IndexCardViewModel(
                title=title, value="", note=_("No data"), state="empty"
            )

        return IndexCardViewModel(
            title=title,
            value=str(dry.delta),
            note=dry.date.strftime("%Y-%m-%d"),
            state="neutral",
        )

    def _card_std_drinks(self) -> IndexCardViewModel:
        title = _("Std drinks")
        total_quantity = self._drink_stats.yearly.total_quantity

        if not total_quantity:
            return IndexCardViewModel(
                title=title, value="", note=_("No data"), state="empty"
            )

        stdav = self._drink_stats.yearly.stdav

        return IndexCardViewModel(
            title=title,
            value=f"{stdav:.0f}",
            note=_("Std Av this year"),
            state="neutral",
        )

    def _card_avg_per_day(self) -> IndexCardViewModel:
        title = _("Avg per day")

        if not self._drink_stats.yearly.total_quantity:
            return IndexCardViewModel(
                title=title, value="", note=_("No data"), state="empty"
            )

        avg = self._drink_stats.yearly.avg_daily_volume_ml
        value = f"{avg:.0f} ml"

        if not self._target:
            return IndexCardViewModel(
                title=title, value=value, note=_("No limit set"), state="neutral"
            )

        under_limit = avg <= self._target
        diff = abs(self._target - avg)
        note = f"{diff:.0f} ml " + (
            _("under the limit") if under_limit else _("over the limit")
        )

        return IndexCardViewModel(
            title=title,
            value=value,
            note=note,
            state="positive" if under_limit else "negative",
        )

    def _card_pure_alcohol(self) -> IndexCardViewModel:
        title = _("Pure alcohol")

        if not self._drink_stats.yearly.total_quantity:
            return IndexCardViewModel(
                title=title, value="", note=_("No data"), state="empty"
            )

        return IndexCardViewModel(
            title=title,
            value=f"{self._drink_stats.yearly.pure_alcohol_liters:.1f} L",
            note=_("this year"),
            state="neutral",
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
        year = year or self._today.year

        _year = self._today.year
        _month = self._today.month
        _week = int(self._today.strftime("%V"))
        _day = self._today.timetuple().tm_yday

        if _year == year:
            return (_day, _week, _month)

        _days = ydays(year)
        _weeks = dt_date(year, 12, 28).isocalendar()[1]

        return (_days, _weeks, 12)
