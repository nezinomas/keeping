import calendar
from datetime import date, datetime
from typing import List

from . import utils


def current_day(year: int, month: int, return_past_day: bool = True) -> int:
    year = year if year else datetime.now().year
    month = month if month else datetime.now().month

    _year = datetime.now().year
    _month = datetime.now().month
    _day = datetime.now().day

    if _year == year and _month == month:
        return _day

    if return_past_day:
        return calendar.monthrange(year, month)[1]

    return None


def year_month_list(year: int = None) -> List[date]:
    '''
    returns: list of months for selected year e.g.
    [datetime.date(1970, 1, 1), datetime.date(1970, 2, 1), ...]
    '''
    year = year if year else datetime.now().year
    months = []

    for i in range(1, 13):
        months.append(date(year, i, 1))

    return months


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

    return calendar.monthlen(year, month)


def years() -> List[int]:
    now = datetime.now().year
    start = now

    try:
        start = utils.get_user().date_joined.year
    except AttributeError:
        pass

    _years = [x for x in range(start, now + 2)]

    return _years


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

    return date(year, 12, 31).isocalendar()[1]
