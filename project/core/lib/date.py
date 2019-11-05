import calendar
from datetime import date, datetime
from typing import List


def current_day(year: int, month: int) -> int:
    year = year if year else datetime.now().year
    month = month if month else datetime.now().month

    _year = datetime.now().year
    _month = datetime.now().month
    _day = datetime.now().day

    if _year == year and _month == month:
        return _day
    else:
        return calendar.monthrange(year, month)[1]


def year_month_list(year: int) -> List[date]:
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
    return calendar.month_name[month].lower()


def monthnames() -> List[str]:
    return [x.lower() for x in calendar.month_name[1:]]


def monthlen(year: int, monthname: str) -> int:
    month = datetime.strptime(monthname, "%B").month
    return calendar.monthlen(year, month)


def years() -> List[int]:
    now = datetime.now().year + 2
    years = [x for x in range(2004, now)]

    return years
