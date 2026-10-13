import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from django.utils.functional import Promise
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


@dataclass(frozen=True)
class DayCell:
    day_date: date
    level: int
    qty: float
    gap: int
    is_today: bool
    is_future: bool


@dataclass(frozen=True)
class CalendarTitles:
    quantity: str | Promise
    empty: str


@dataclass(frozen=True)
class CalendarDays:
    boundary: YearBoundary
    val_by_date: dict[date, float]
    qty_by_date: dict[date, float]
    gap_by_date: dict[date, int]
    today_gap: int
    thresholds: Sequence[float]

    @classmethod
    def from_rows(
        cls,
        boundary: YearBoundary,
        daily_data: Sequence[dict],
        earlier: PastRecord | NoPastRecord,
        value_key: str,
        thresholds: Sequence[float],
    ) -> "CalendarDays":
        today = boundary.today
        past_dates = [row["date"] for row in daily_data if row["date"] <= today]
        latest = earlier
        if past_dates:
            latest = PastRecord(max(past_dates))

        return cls(
            boundary=boundary,
            val_by_date={row["date"]: row.get(value_key, 0.0) for row in daily_data},
            qty_by_date={
                row["date"]: row.get("qty", row.get(value_key, 0.0))
                for row in daily_data
            },
            gap_by_date=Stats(data=daily_data, earlier=earlier).gap_by_date(),
            today_gap=latest.days_to(today),
            thresholds=thresholds,
        )

    def cell(self, day_date: date) -> DayCell:
        boundary = self.boundary
        level = _calc_level(self.val_by_date.get(day_date, 0.0), self.thresholds)
        is_today = day_date == boundary.today
        gap = self.gap_by_date.get(day_date, 0)

        if is_today and level == 0:
            gap = self.today_gap

        return DayCell(
            day_date=day_date,
            level=level,
            qty=self.qty_by_date.get(day_date, 0.0),
            gap=gap,
            is_today=is_today,
            is_future=day_date > boundary.end_date,
        )


def _fmt(bound: float) -> str:
    return f"{bound:g}"


def _calc_level(val: float, thresholds: Sequence[float]) -> int:
    if val <= 0:
        return 0
    return 1 + sum(1 for bound in thresholds if val >= bound)


def _label(cell: DayCell, titles: CalendarTitles) -> str:
    stamp = f"{cell.day_date:%Y-%m-%d}"
    gap_title = _("Gap")

    if cell.level:
        return f"{stamp}\n{titles.quantity}: {cell.qty:.1f}\n{gap_title}: {cell.gap}d."
    if cell.is_future:
        return ""
    if cell.is_today:
        return f"{stamp}\n{gap_title}: {cell.gap}d."

    return "\n".join(filter(None, (stamp, titles.empty)))


class CalendarGrid:
    @classmethod
    def build(
        cls,
        boundary: YearBoundary,
        daily_data: Sequence[dict] = (),
        earlier: PastRecord | NoPastRecord = NoPastRecord(),
        quantity_title: str | Promise = _lazy("Quantity"),
        empty_title: str = "",
        unit: str = "",
        # no thresholds means presence, not a scale nobody configured
        thresholds: Sequence[float] = (),
        # the column the levels are read off, where it is not the one displayed
        value_key: str = "qty",
        low_title: str = "",
        high_title: str = "",
    ) -> CalendarYearViewModel:
        calendar_days = CalendarDays.from_rows(
            boundary, daily_data, earlier, value_key, thresholds
        )
        titles = CalendarTitles(quantity=quantity_title, empty=empty_title)
        names = list(month_names().values())

        months = [
            cls._build_month(calendar_days, month, titles, names[month - 1])
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
        calendar_days: CalendarDays,
        month: int,
        titles: CalendarTitles,
        name: str,
    ) -> CalendarMonthViewModel:
        year = calendar_days.boundary.year
        total_days = calendar.monthrange(year, month)[1]

        return CalendarMonthViewModel(
            name=name,
            number=month,
            leading_blanks=date(year, month, 1).weekday(),
            days=[
                cls._build_day(calendar_days.cell(date(year, month, day)), titles)
                for day in range(1, total_days + 1)
            ],
        )

    @staticmethod
    def _build_day(cell: DayCell, titles: CalendarTitles) -> CalendarDayViewModel:

        return CalendarDayViewModel(
            day=cell.day_date.day,
            level=cell.level,
            is_today=cell.is_today,
            is_future=cell.is_future,
            label=_label(cell, titles),
            gap=cell.gap,
        )
