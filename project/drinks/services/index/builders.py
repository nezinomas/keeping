from dataclasses import asdict, dataclass, field
from datetime import date as dt_date
from datetime import datetime

from django.utils.translation import gettext as _

from ....core.lib.date import ydays
from ....core.lib.translation import month_names
from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DrinkStats


@dataclass(frozen=True)
class ChartViewModel:
    categories: list[str]
    data: list[float]
    text: dict[str, str]
    target: float | None = None
    avg: float | None = None

    @property
    def as_dict(self) -> dict:
        """Bridges the gap between strict DTOs and Django's json_script"""
        return asdict(self)


@dataclass(frozen=True)
class DryDaysViewModel:
    date: dt_date | None = None
    delta: int = 0

    @property
    def has_data(self) -> bool:
        """Allows templates to cleanly check {% if dry_days.has_data %}"""
        return self.date is not None


@dataclass(frozen=True)
class ConsumptionViewModel:
    qty: float
    avg: float
    target: float


@dataclass(frozen=True)
class AlcoholViewModel:
    liters: float


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


class IndexBuilder:
    def __init__(
        self,
        converter: DrinkConverter,
        drink_stats: DrinkStats,
        target: float = 0.0,
        latest_past_date: dt_date | None = None,
        latest_current_date: dt_date | None = None,
        today: dt_date | None = None,  # Dependency injection fixes the testing trap
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

    def tbl_consumption(self) -> ConsumptionViewModel:
        return ConsumptionViewModel(
            qty=self._drink_stats.yearly.total_quantity,
            avg=self._drink_stats.yearly.avg_daily_volume_ml,
            target=self._target,
        )

    def tbl_alcohol(self) -> AlcoholViewModel:
        stdav = self._drink_stats.yearly.total_quantity / self._converter.ratio
        return AlcoholViewModel(liters=self._converter.stdav_to_alcohol(stdav))

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

        # Pre-calculate base math for readability
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
        """Helper factory method to keep standard conversions clean"""
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
