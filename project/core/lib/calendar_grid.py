import calendar
from dataclasses import dataclass
from datetime import date

from django.utils.translation import gettext as _

from ...counts.lib.stats import Stats as CountStats
from ...drinks.lib.drinks_risk import HEAVY_DAY_STDAV
from .translation import month_names
from .year_boundary import YearBoundary

LEVEL_1_MAX = 2.0
LEVEL_2_MAX = 4.0
LEVEL_3_MAX = HEAVY_DAY_STDAV


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


@dataclass(frozen=True)
class CalendarYearViewModel:
    months: list[CalendarMonthViewModel]
    legend: CalendarLegendViewModel = CalendarLegendViewModel(bounds=())


def _fmt(bound: float) -> str:
    return f"{bound:g}"


def _calc_level(val: float) -> int:
    if val <= 0:
        return 0
    if val < LEVEL_1_MAX:
        return 1
    if val < LEVEL_2_MAX:
        return 2
    if val < LEVEL_3_MAX:
        return 3
    return 4


class CalendarGrid:
    @classmethod
    def build(
        cls,
        year: int,
        daily_data: list[dict] | None = None,
        latest_past_date: date | None = None,
        today: date | None = None,
        quantity_title: str | None = None,
        unit: str = "",
    ) -> CalendarYearViewModel:
        boundary = YearBoundary.for_year(year, today)
        today = boundary.today
        daily_data = daily_data or []
        quantity_title = quantity_title or _("Quantity")

        val_key = "stdav" if daily_data and "stdav" in daily_data[0] else "qty"

        val_by_date = {row["date"]: row.get(val_key, 0.0) for row in daily_data}
        qty_by_date = {
            row["date"]: row.get("qty", row.get(val_key, 0.0)) for row in daily_data
        }

        gap_by_date = {}
        if daily_data:
            stats = CountStats(year=year, data=daily_data, past_latest=latest_past_date)
            gaps_df = stats._calculate_gaps()
            if not gaps_df.is_empty():
                gap_by_date = {
                    row["date"]: int(row["duration"]) for row in gaps_df.to_dicts()
                }

        today_gap = 0
        latest_drink = None
        if daily_data:
            past_drinks = [row["date"] for row in daily_data if row["date"] <= today]
            if past_drinks:
                latest_drink = max(past_drinks)
        if not latest_drink:
            latest_drink = latest_past_date

        if latest_drink and today >= latest_drink:
            today_gap = (today - latest_drink).days

        months = [
            cls._build_month(
                boundary,
                month,
                val_by_date,
                qty_by_date,
                gap_by_date,
                today_gap,
                quantity_title,
            )
            for month in range(1, 13)
        ]

        return CalendarYearViewModel(months=months, legend=cls._legend(unit))

    @staticmethod
    def _legend(unit: str) -> CalendarLegendViewModel:
        return CalendarLegendViewModel(
            bounds=(
                "0",
                f"<{_fmt(LEVEL_1_MAX)}",
                f"{_fmt(LEVEL_1_MAX)}-{_fmt(LEVEL_2_MAX)}",
                f"{_fmt(LEVEL_2_MAX)}-{_fmt(LEVEL_3_MAX)}",
                f">={_fmt(LEVEL_3_MAX)}",
            ),
            unit=unit,
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
    ) -> CalendarDayViewModel:
        level = _calc_level(val_by_date.get(day_date, 0.0))
        qty = qty_by_date.get(day_date, 0.0)
        gap = gap_by_date.get(day_date, 0)
        is_today = day_date == boundary.today

        is_future = day_date > boundary.end_date

        if level == 0:
            label = f"{day_date:%Y-%m-%d}\n{_('No drink')}"
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
