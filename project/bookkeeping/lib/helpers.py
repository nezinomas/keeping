import calendar
from datetime import date, datetime
from typing import List


def calc_percent(args):
    market = args[0]
    invested = args[1]

    if market and invested:
        return ((market * 100) / invested) - 100
    else:
        return 0.0


def calc_sum(args):
    market = args[0]
    invested = args[1]

    if market:
        return market - invested
    else:
        return 0.0


def create_month_list(year: int) -> List[date]:
    months = []
    for i in range(1, 13):
        months.append(date(year, i, 1))
    return months


def current_day(year: int, month: int) -> int:
    _year = datetime.now().year
    _month = datetime.now().month
    _day = datetime.now().day

    if _year == year and _month == month:
        return _day
    else:
        return calendar.monthrange(year, month)[1]
