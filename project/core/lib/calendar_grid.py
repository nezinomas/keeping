import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from django.utils.dates import MONTHS_3
from django.utils.translation import gettext as _

from .day_stats import Stats
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

    @property
    def abbr(self) -> str:
        return str(MONTHS_3[self.number])


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


class CalendarGrid:
    @classmethod
    def build(
        cls,
        year: int,
        daily_data: list[dict] | None = None,
        latest_past_date: date | None = None,
        today: date | None = None,
        quantity_title: str | None = None,
        empty_title: str | None = None,
        unit: str = "",
        # no thresholds means presence, not a scale nobody configured
        thresholds: Sequence[float] = (),
        low_title: str = "",
        high_title: str = "",
    ) -> CalendarYearViewModel:
        boundary = YearBoundary.for_year(year, today)
        today = boundary.today
        daily_data = daily_data or []
        quantity_title = quantity_title or _("Quantity")
        empty_title = empty_title or _("No drink")

        val_key = "stdav" if daily_data and "stdav" in daily_data[0] else "qty"

        val_by_date = {row["date"]: row.get(val_key, 0.0) for row in daily_data}
        qty_by_date = {
            row["date"]: row.get("qty", row.get(val_key, 0.0)) for row in daily_data
        }

        gap_by_date = {}
        if daily_data:
            stats = Stats(year=year, data=daily_data, past_latest=latest_past_date)
            gaps_df = stats._calculate_gaps()
            if not gaps_df.is_empty():
                gap_by_date = {
                    row["date"]: int(row["duration"]) for row in gaps_df.to_dicts()
                }

        today_gap = 0
        latest_recorded = None
        if daily_data:
            past_dates = [row["date"] for row in daily_data if row["date"] <= today]
            if past_dates:
                latest_recorded = max(past_dates)
        if not latest_recorded:
            latest_recorded = latest_past_date

        if latest_recorded and today >= latest_recorded:
            today_gap = (today - latest_recorded).days

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
        if thresholds:
            bounds = (
                "0",
                f"<{_fmt(thresholds[0])}",
                *(
                    f"{_fmt(low)}-{_fmt(high)}"
                    for low, high in zip(thresholds, thresholds[1:], strict=False)
                ),
                f">={_fmt(thresholds[-1])}",
            )
        else:
            bounds = ("0", ">0")

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

        if level == 0:
            label = f"{day_date:%Y-%m-%d}\n{empty_title}"
            if is_today:
                gap_title = _("Gap")
                label = f"{day_date:%Y-%m-%d}\n{gap_title}: {today_gap}d."
                gap = today_gap
            if is_future:
                label = ""
        else:
            gap_title = _("Gap")
            label = (
                f"{day_date:%Y-%m-%d}\n"
                f"{quantity_title}: {qty:.1f}\n"
                f"{gap_title}: {gap}d."
            )

        return CalendarDayViewModel(
            day=day_date.day,
            level=level,
            is_today=is_today,
            is_future=is_future,
            label=label,
            gap=gap,
        )
