from datetime import date

from ...core.lib.calendar_grid import (
    CalendarDayViewModel,
    CalendarGrid,
    CalendarMonthViewModel,
    CalendarYearViewModel,
)

__all__ = [
    "CalendarDayViewModel",
    "CalendarMonthViewModel",
    "CalendarYearViewModel",
    "CalendarChart",
]


class CalendarChart:
    def __init__(
        self,
        year: int,
        drink_type: str = "stdav",
        daily_data: list[dict] | None = None,
        latest_past_date: date | None = None,
    ):
        self.year = year
        self.drink_type = drink_type
        self.daily_data = daily_data or []
        self.latest_past_date = latest_past_date

    def year_grid(self, today: date | None = None) -> CalendarYearViewModel:
        return CalendarGrid.build(
            year=self.year,
            daily_data=self.daily_data,
            latest_past_date=self.latest_past_date,
            today=today,
        )
