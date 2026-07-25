from datetime import date

import pytest
import time_machine
from django.utils.translation import gettext as _

from ...lib.drinks_options import DrinkConverter
from ...services.calendar_chart import (
    CalendarChart,
    CalendarDayViewModel,
    CalendarMonthViewModel,
    CalendarYearViewModel,
)
from ...services.model_services import DrinkModelService
from ..factories import DrinkFactory

pytestmark = pytest.mark.django_db


def _calendar(year=1999, drink_type="beer", daily_data=None, latest_past_date=None):
    return CalendarChart(
        year=year,
        drink_type=drink_type,
        daily_data=daily_data or [],
        latest_past_date=latest_past_date,
    )


# -------------------------------------------------------------------------------------
#                                                          CalendarChart.year_grid
# -------------------------------------------------------------------------------------
@time_machine.travel("1999-06-15")
def test_year_grid_empty_returns_full_year():
    grid = _calendar(daily_data=[]).year_grid()

    assert isinstance(grid, CalendarYearViewModel)
    assert len(grid.months) == 12
    assert all(isinstance(m, CalendarMonthViewModel) for m in grid.months)
    assert all(isinstance(d, CalendarDayViewModel) for m in grid.months for d in m.days)
    assert all(d.level == 0 for m in grid.months for d in m.days)
    assert all(d.label == "" for m in grid.months for d in m.days)


def test_year_grid_month_metadata():
    grid = _calendar(daily_data=[]).year_grid(today=date(1999, 12, 31))

    jan = grid.months[0]
    assert jan.number == 1
    assert len(jan.days) == 31
    assert jan.leading_blanks == date(1999, 1, 1).weekday()  # Friday -> 4

    feb = grid.months[1]
    assert feb.number == 2
    assert len(feb.days) == 28
    assert feb.leading_blanks == date(1999, 2, 1).weekday()  # Monday -> 0


def test_year_grid_levels_and_labels():
    daily = [
        {"date": date(1999, 1, 1), "stdav": 1.0, "qty": 0.4},  # level 1
        {"date": date(1999, 1, 2), "stdav": 2.0, "qty": 0.8},  # level 2
        {"date": date(1999, 1, 3), "stdav": 4.0, "qty": 1.6},  # level 3
        {"date": date(1999, 1, 4), "stdav": 6.0, "qty": 2.4},  # level 4
        {"date": date(1999, 1, 5), "stdav": 0.0, "qty": 0.0},  # level 0
    ]

    days = (
        _calendar(daily_data=daily).year_grid(today=date(1999, 12, 31)).months[0].days
    )

    gap_str = _("Gap")
    assert [d.level for d in days[:5]] == [1, 2, 3, 4, 0]
    assert days[0].label == f"1999-01-01 · {gap_str} 0d. · 0.4"
    assert days[3].label == f"1999-01-04 · {gap_str} 1d. · 2.4"
    assert days[4].label == ""
    assert days[0].gap == 0
    assert days[3].gap == 1


def test_year_grid_gaps_with_latest_past_date():
    daily = [
        {"date": date(1999, 1, 10), "stdav": 1.0, "qty": 0.5},
        {"date": date(1999, 1, 15), "stdav": 2.0, "qty": 1.0},
    ]
    grid = _calendar(daily_data=daily, latest_past_date=date(1999, 1, 5)).year_grid(
        today=date(1999, 12, 31)
    )

    jan_days = grid.months[0].days
    day_10 = jan_days[9]
    day_15 = jan_days[14]

    gap_str = _("Gap")
    assert day_10.gap == 5
    assert day_10.label == f"1999-01-10 · {gap_str} 5d. · 0.5"
    assert day_15.gap == 5
    assert day_15.label == f"1999-01-15 · {gap_str} 5d. · 1.0"


def test_year_grid_today_and_future_flags():
    grid = _calendar(daily_data=[]).year_grid(today=date(1999, 6, 15))

    june = grid.months[5].days
    assert june[14].is_today is True  # 15th
    assert june[14].is_future is False
    assert june[15].is_future is True  # 16th
    # a past month has no future days
    assert all(not d.is_future for d in grid.months[0].days)


def test_year_grid_other_year_has_no_future_days():
    grid = _calendar(year=1998, daily_data=[]).year_grid(today=date(1999, 6, 15))

    assert all(not d.is_future for m in grid.months for d in m.days)


# -------------------------------------------------------------------------------------
#                                        Highcharts halves (still used elsewhere)
# -------------------------------------------------------------------------------------
def test_calendar_halves_split_the_year():
    daily = [{"date": date(1999, 1, 2), "stdav": 2.5, "qty": 1.0}]
    calendar = _calendar(daily_data=daily)

    first = calendar.first_half_of_year()
    second = calendar.second_half_of_year()

    assert len(first["data"]) == 6
    assert len(second["data"]) == 6
    assert "categories" in first
    assert first["ratio"] == DrinkConverter("beer").stdav_per_unit


@time_machine.travel("1999-1-1")
def test_calendar_first_record_with_gap_from_previous_year(main_user):
    DrinkFactory(date=date(1999, 1, 2), stdav=2.5)
    DrinkFactory(date=date(1998, 1, 1), stdav=2.5)

    daily = DrinkModelService(main_user).sum_by_day(1999)
    data = _calendar(
        drink_type=main_user.drink_type,
        daily_data=daily,
        latest_past_date=date(1998, 1, 1),
    ).first_half_of_year()["data"][0]["data"]

    assert data[4] == [0, 4, 0.0005, 53, "1999-01-01"]
    assert data[5] == [0, 5, 1.0, 53, "1999-01-02", 1.0, 366.0]
