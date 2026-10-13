import calendar
from datetime import date, datetime

from ...users.models import User
from .year_boundary import YearBoundary


def current_day(year: int, month: int, return_past_day: bool = True) -> int:
    today = date.today()

    if today.year == year and today.month == month:
        return today.day

    if return_past_day:
        return calendar.monthrange(year, month)[1]

    return 0


def year_month_list(year: int) -> list[date]:
    return [date(year, i, 1) for i in range(1, 13)]


def monthnames() -> list[str]:
    return [x.lower() for x in calendar.month_name[1:]]


def latest_year() -> int:
    return datetime.now().year + 1


def years(user: User) -> list[int]:
    return list(range(user.journal.first_record.year, latest_year() + 1))


def years_to_date(user: User) -> list[int]:
    return list(range(user.journal.first_record.year, datetime.now().year + 1))


def set_date_with_user_year(user):
    now = datetime.now()
    day = min(now.day, calendar.monthrange(user.year, now.month)[1])

    return datetime(user.year, now.month, day)


def yday(year: int, today: date) -> tuple[int, int]:
    """Days of the year gone by, and days it holds."""
    boundary = YearBoundary(year, today)

    elapsed = 0
    if year <= boundary.today.year:
        elapsed = boundary.days_elapsed

    return (elapsed, ydays(boundary.year))


def ydays(year: int) -> int:
    return 366 if calendar.isleap(year) else 365
