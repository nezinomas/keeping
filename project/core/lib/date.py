import calendar
from datetime import date, datetime
from typing import List


def create_month_list(year: int) -> List[date]:
    year = year if year else datetime.now().year
    months = []

    for i in range(1, 13):
        months.append(date(year, i, 1))
    return months


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


def month_name(month: int) -> str:
    return calendar.month_name[month].lower()


def months():
    return [x.lower() for x in calendar.month_name[1:]]


def month_days(year: int, month_name: str) -> int:
    month = datetime.strptime(month_name, "%B").month
    return calendar.monthlen(year, month)
