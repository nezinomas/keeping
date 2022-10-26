import calendar
import contextlib
from datetime import date, datetime
from typing import List, Tuple

from . import utils


def current_day(year: int, month: int, return_past_day: bool = True) -> int:
    year = year or datetime.now().year
    month = month or datetime.now().month

    _year = datetime.now().year
    _month = datetime.now().month
    _day = datetime.now().day

    if _year == year and _month == month:
        return _day

    return calendar.monthrange(year, month)[1] if return_past_day else None


def year_month_list(year: int = None) -> List[date]:
    '''
    returns: list of months for selected year e.g.
    [datetime.date(1970, 1, 1), datetime.date(1970, 2, 1), ...]
    '''
    year = year or datetime.now().year
    return [date(year, i, 1) for i in range(1, 13)]


def monthname(month: int) -> str:
    try:
        _month = calendar.month_name[month]
    except (TypeError, IndexError):
        return 'january'

    return _month.lower()


def monthnames() -> List[str]:
    return [x.lower() for x in calendar.month_name[1:]]


def monthlen(year: int, month_name: str) -> int:
    if month_name not in monthnames():
        return 31

    month = datetime.strptime(month_name, "%B").month

    return calendar.monthrange(year, month)[1]


def years() -> List[int]:
    now = datetime.now().year
    start = now

    with contextlib.suppress(AttributeError):
        start = utils.get_user().journal.first_record.year

    return list(range(start, now + 2))


def set_year_for_form():
    now = datetime.now()
    month = now.month
    day = now.day
    year = utils.get_user().year

    return datetime(year, month, day)


def weeknumber(year: int):
    _current_year = datetime.now().year

    if _current_year == year:
        return datetime.now().isocalendar()[1]

    # year have 53 weeks if starts on Wednesday or year is leap
    weekday = date(year, 1, 1).weekday()  # 0=Monday
    isleap = calendar.isleap(year)

    return 53 if weekday == 2 or isleap else 52


def yday(year: int) -> Tuple[int, int]:
    now = datetime.now().date()
    year = year or now.year

    _year = now.year
    _days = ydays(year)

    if _year == year:
        _day = now.timetuple().tm_yday
        return (_day, _days)

    return (_days, _days)


def ydays(year: int) -> int:
    return 366 if calendar.isleap(year) else 365
