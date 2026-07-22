import calendar
from dataclasses import dataclass, field
from datetime import date

from django.utils.translation import gettext as _

from ...core.lib.translation import month_names, weekday_names
from ...counts.lib.stats import Calendar
from ...counts.lib.stats import Stats as CountStats
from ..lib.drinks_options import DrinkConverter
from ..services.model_services import DrinkModelService

# Std Av (stdav) thresholds that bucket a day into a heatmap intensity level.
# level 0: stdav <= 0 (dry / no record)
# level 1: 0 < stdav < LEVEL_1_MAX
# level 2: LEVEL_1_MAX <= stdav < LEVEL_2_MAX
# level 3: LEVEL_2_MAX <= stdav < LEVEL_3_MAX
# level 4: stdav >= LEVEL_3_MAX
LEVEL_1_MAX = 2.0
LEVEL_2_MAX = 4.0
LEVEL_3_MAX = 6.0


@dataclass(frozen=True)
class CalendarDayViewModel:
    day: int
    level: int  # 0 = dry/no record; 1..4 = increasing intensity
    is_today: bool = False
    is_future: bool = False
    label: str = ""  # tooltip text; "" for dry days, else f"{iso_date} · {qty:.1f}"


@dataclass(frozen=True)
class CalendarMonthViewModel:
    name: str  # localized month name
    number: int  # 1..12
    leading_blanks: int  # 0..6 = Monday-based weekday index of day 1
    days: list[CalendarDayViewModel]


@dataclass(frozen=True)
class CalendarYearViewModel:
    months: list[CalendarMonthViewModel]


def _stdav_level(stdav: float) -> int:
    if stdav <= 0:
        return 0
    if stdav < LEVEL_1_MAX:
        return 1
    if stdav < LEVEL_2_MAX:
        return 2
    if stdav < LEVEL_3_MAX:
        return 3
    return 4


@dataclass
class CalendarChart:
    year: int
    drink_type: str
    daily_data: DrinkModelService.sum_by_day
    latest_past_date: date = None

    chart_data: list[dict] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.converter = DrinkConverter(self.drink_type)

        if not self.daily_data:
            return

        stats = CountStats(
            year=self.year, data=self.daily_data, past_latest=self.latest_past_date
        )
        self.chart_data = Calendar(stats).chart_data()

    def full_calendar(self, data: list[dict]) -> dict:
        return {
            "data": data,
            "categories": [name[0] for name in list(weekday_names().values())],
            "ratio": self.converter.stdav_per_unit,
            "text": {
                "gap": _("Gap"),
                "quantity": _("Quantity"),
            },
        }

    def first_half_of_year(self):
        return self.full_calendar(data=self.chart_data[:6])

    def second_half_of_year(self):
        return self.full_calendar(data=self.chart_data[6:])

    def year_grid(self, today: date | None = None) -> CalendarYearViewModel:
        today = today or date.today()

        stdav_by_date = {row["date"]: row["stdav"] for row in self.daily_data}
        qty_by_date = {row["date"]: row["qty"] for row in self.daily_data}

        months = [
            self._build_month(month, today, stdav_by_date, qty_by_date)
            for month in range(1, 13)
        ]

        return CalendarYearViewModel(months=months)

    def _build_month(
        self,
        month: int,
        today: date,
        stdav_by_date: dict[date, float],
        qty_by_date: dict[date, float],
    ) -> CalendarMonthViewModel:
        first_day = date(self.year, month, 1)
        total_days = calendar.monthrange(self.year, month)[1]

        days = [
            self._build_day(
                date(self.year, month, day), today, stdav_by_date, qty_by_date
            )
            for day in range(1, total_days + 1)
        ]

        return CalendarMonthViewModel(
            name=list(month_names().values())[month - 1],
            number=month,
            leading_blanks=first_day.weekday(),
            days=days,
        )

    def _build_day(
        self,
        day_date: date,
        today: date,
        stdav_by_date: dict[date, float],
        qty_by_date: dict[date, float],
    ) -> CalendarDayViewModel:
        level = _stdav_level(stdav_by_date.get(day_date, 0.0))
        qty = qty_by_date.get(day_date, 0.0)

        label = "" if level == 0 else f"{day_date:%Y-%m-%d} · {qty:.1f}"

        return CalendarDayViewModel(
            day=day_date.day,
            level=level,
            is_today=day_date == today,
            is_future=day_date > today and self.year == today.year,
            label=label,
        )
