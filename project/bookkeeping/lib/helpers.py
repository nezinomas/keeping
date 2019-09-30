import calendar
from datetime import date, datetime
from typing import Dict, List


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


def get_value_from_dict(arr: Dict, month: int) -> float:
    return float(arr.get(month_name(month), 0.0)) if arr else 0.0
