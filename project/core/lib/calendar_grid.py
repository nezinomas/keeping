import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from .day_stats import NoPastRecord, PastRecord, Stats
from .translation import month_names
from .year_boundary import YearBoundary


@dataclass(frozen=True)
class CalendarDayViewModel:
    day: int
    level: int
    is_today: bool = False
    is_future: bool = False
    label: str = ""
    gap: int = 0

    @property
    def speech(self) -> str:
        return self.label.replace("\n", ", ")


@dataclass(frozen=True)
class CalendarMonthViewModel:
    name: str
    number: int
    leading_blanks: int
    days: list[CalendarDayViewModel]


@dataclass(frozen=True)
class CalendarLegendViewModel:
    bounds: tuple[str, ...]
    unit: str = ""
    low_title: str = ""
    high_title: str = ""


@dataclass(frozen=True)
class CalendarYearViewModel:
    months: list[CalendarMonthViewModel]
    legend: CalendarLegendViewModel = CalendarLegendViewModel(bounds=())


def _fmt(bound: float) -> str:
    return f"{bound:g}"


def _calc_level(val: float, thresholds: Sequence[float]) -> int:
    if val <= 0:
        return 0
    return 1 + sum(1 for bound in thresholds if val >= bound)


def _label(
    day_date: date,
    level: int,
    qty: float,
    gap: int,
    quantity_title: str,
    empty_title: str,
    is_today: bool,
    is_future: bool,
) -> str:
    stamp = f"{day_date:%Y-%m-%d}"
    gap_title = _("Gap")

    if level:
        return f"{stamp}\n{quantity_title}: {qty:.1f}\n{gap_title}: {gap}d."
    if is_future:
        return ""
    if is_today:
        return f"{stamp}\n{gap_title}: {gap}d."

    return "\n".join(filter(None, (stamp, empty_title)))


class CalendarGrid:
    @classmethod
    def build(
        cls,
        boundary: YearBoundary,
        daily_data: Sequence[dict] = (),
        earlier: PastRecord | NoPastRecord = NoPastRecord(),
        quantity_title: str = _lazy("Quantity"),
        empty_title: str = "",
        unit: str = "",
        # no thresholds means presence, not a scale nobody configured
        thresholds: Sequence[float] = (),
        # the column the levels are read off, where it is not the one displayed
        value_key: str = "qty",
        low_title: str = "",
        high_title: str = "",
    ) -> CalendarYearViewModel:
        today = boundary.today

        val_by_date = {row["date"]: row.get(value_key, 0.0) for row in daily_data}
        qty_by_date = {
            row["date"]: row.get("qty", row.get(value_key, 0.0)) for row in daily_data
        }

        gap_by_date = Stats(data=daily_data, earlier=earlier).gap_by_date()

        past_dates = [row["date"] for row in daily_data if row["date"] <= today]
        latest = earlier
        if past_dates:
            latest = PastRecord(max(past_dates))

        today_gap = latest.days_to(today)

        months = [
            cls._build_month(
                boundary,
                month,
                val_by_date,
                qty_by_date,
                gap_by_date,
                today_gap,
                quantity_title,
                empty_title,
                thresholds,
            )
            for month in range(1, 13)
        ]

        return CalendarYearViewModel(
            months=months,
            legend=cls._legend(unit, thresholds, low_title, high_title),
        )

    @staticmethod
    def _legend(
        unit: str,
        thresholds: Sequence[float],
        low_title: str,
        high_title: str,
    ) -> CalendarLegendViewModel:
        bounds = ("0", "≥1")

        if thresholds:
            bounds = (
                "0",
                f"<{_fmt(thresholds[0])}",
                *(
                    f"{_fmt(low)}-{_fmt(high)}"
                    for low, high in zip(thresholds, thresholds[1:], strict=False)
                ),
                f"≥{_fmt(thresholds[-1])}",
            )

        return CalendarLegendViewModel(
            bounds=bounds,
            unit=unit,
            low_title=low_title,
            high_title=high_title,
        )

    @classmethod
    def _build_month(
        cls,
        boundary: YearBoundary,
        month: int,
        val_by_date: dict[date, float],
        qty_by_date: dict[date, float],
        gap_by_date: dict[date, int],
        today_gap: int,
        quantity_title: str,
        empty_title: str,
        thresholds: Sequence[float],
    ) -> CalendarMonthViewModel:
        year = boundary.year
        first_day = date(year, month, 1)
        total_days = calendar.monthrange(year, month)[1]

        days = [
            cls._build_day(
                boundary,
                date(year, month, day),
                val_by_date,
                qty_by_date,
                gap_by_date,
                today_gap,
                quantity_title,
                empty_title,
                thresholds,
            )
            for day in range(1, total_days + 1)
        ]

        return CalendarMonthViewModel(
            name=list(month_names().values())[month - 1],
            number=month,
            leading_blanks=first_day.weekday(),
            days=days,
        )

    @classmethod
    def _build_day(
        cls,
        boundary: YearBoundary,
        day_date: date,
        val_by_date: dict[date, float],
        qty_by_date: dict[date, float],
        gap_by_date: dict[date, int],
        today_gap: int,
        quantity_title: str,
        empty_title: str,
        thresholds: Sequence[float],
    ) -> CalendarDayViewModel:
        level = _calc_level(val_by_date.get(day_date, 0.0), thresholds)
        qty = qty_by_date.get(day_date, 0.0)
        gap = gap_by_date.get(day_date, 0)
        is_today = day_date == boundary.today
        is_future = day_date > boundary.end_date

        if is_today and level == 0:
            gap = today_gap

        label = _label(
            day_date, level, qty, gap, quantity_title, empty_title, is_today, is_future
        )

        return CalendarDayViewModel(
            day=day_date.day,
            level=level,
            is_today=is_today,
            is_future=is_future,
            label=label,
            gap=gap,
        )
