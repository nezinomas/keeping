import calendar
from datetime import date, datetime

from ...users.models import User
from .year_boundary import YearBoundary


def current_day(
    year: int, month: int, today: date, return_past_day: bool = True
) -> int:
    if today.year == year and today.month == month:
        return today.day

    if return_past_day:
        return calendar.monthrange(year, month)[1]

    return 0


def year_month_list(year: int) -> list[date]:
    return [date(year, i, 1) for i in range(1, 13)]


def monthnames() -> list[str]:
    return [x.lower() for x in calendar.month_name[1:]]


def latest_year(today: date) -> int:
    return today.year + 1


def years(user: User, today: date) -> list[int]:
    return list(range(user.journal.first_record.year, latest_year(today) + 1))


def years_to_date(user: User, today: date) -> list[int]:
    return list(range(user.journal.first_record.year, today.year + 1))


def set_date_with_user_year(user: User, today: date) -> datetime:
    year = user.selected_year()
    day = min(today.day, calendar.monthrange(year, today.month)[1])

    return datetime(year, today.month, day)


def yday(year: int, today: date) -> tuple[int, int]:
    """Days of the year gone by, and days it holds."""
    boundary = YearBoundary(year, today)

    elapsed = 0
    if year <= boundary.today.year:
        elapsed = boundary.days_elapsed

    return (elapsed, ydays(boundary.year))


def ydays(year: int) -> int:
    return 366 if calendar.isleap(year) else 365
