from datetime import date

import pytest
import time_machine
from django.utils.translation import gettext as _

from ...lib.calendar_grid import (
    CalendarDayViewModel,
    CalendarGrid,
    CalendarMonthViewModel,
    CalendarYearViewModel,
)

pytestmark = pytest.mark.django_db


@time_machine.travel("1999-06-15")
def test_calendar_grid_empty_data():
    grid = CalendarGrid.build(1999)

    assert isinstance(grid, CalendarYearViewModel)
    assert len(grid.months) == 12
    assert all(isinstance(m, CalendarMonthViewModel) for m in grid.months)
    assert all(isinstance(d, CalendarDayViewModel) for m in grid.months for d in m.days)
    assert all(d.level == 0 for m in grid.months for d in m.days)


def test_calendar_grid_levels_and_labels():
    daily = [
        {"date": date(1999, 1, 1), "stdav": 1.0, "qty": 0.4},
        {"date": date(1999, 1, 2), "stdav": 3.0, "qty": 1.2},
        {"date": date(1999, 1, 3), "stdav": 5.0, "qty": 2.0},
        {"date": date(1999, 1, 4), "stdav": 7.0, "qty": 2.8},
    ]
    grid = CalendarGrid.build(1999, daily_data=daily, today=date(1999, 12, 31))

    jan_days = grid.months[0].days
    assert jan_days[0].level == 1
    assert jan_days[1].level == 2
    assert jan_days[2].level == 3
    assert jan_days[3].level == 4

    qty_str = _("Quantity")
    gap_str = _("Gap")
    assert jan_days[0].label == f"1999-01-01\n{qty_str}: 0.4\n{gap_str}: 0d."


def test_calendar_grid_custom_quantity_title():
    daily = [{"date": date(1999, 1, 1), "qty": 5.0}]
    grid = CalendarGrid.build(
        1999, daily_data=daily, today=date(1999, 12, 31), quantity_title="Count"
    )

    jan_days = grid.months[0].days
    assert "Count: 5.0" in jan_days[0].label


@time_machine.travel("1999-06-15")
def test_build_empty_returns_full_year():
    grid = CalendarGrid.build(1999, daily_data=[])

    assert isinstance(grid, CalendarYearViewModel)
    assert len(grid.months) == 12
    assert all(isinstance(m, CalendarMonthViewModel) for m in grid.months)
    assert all(isinstance(d, CalendarDayViewModel) for m in grid.months for d in m.days)
    assert all(d.level == 0 for m in grid.months for d in m.days)
    assert all(d.label == "" for m in grid.months for d in m.days if not d.is_today)
    gap_str = _("Gap")
    assert grid.months[5].days[14].label == f"1999-06-15\n{gap_str}: 0d."


def test_build_month_metadata():
    grid = CalendarGrid.build(1999, daily_data=[], today=date(1999, 12, 31))

    jan = grid.months[0]
    assert jan.number == 1
    assert len(jan.days) == 31
    assert jan.leading_blanks == date(1999, 1, 1).weekday()  # Friday -> 4

    feb = grid.months[1]
    assert feb.number == 2
    assert len(feb.days) == 28
    assert feb.leading_blanks == date(1999, 2, 1).weekday()  # Monday -> 0


def test_build_all_levels_and_labels():
    daily = [
        {"date": date(1999, 1, 1), "stdav": 1.0, "qty": 0.4},  # level 1
        {"date": date(1999, 1, 2), "stdav": 2.0, "qty": 0.8},  # level 2
        {"date": date(1999, 1, 3), "stdav": 4.0, "qty": 1.6},  # level 3
        {"date": date(1999, 1, 4), "stdav": 6.0, "qty": 2.4},  # level 4
        {"date": date(1999, 1, 5), "stdav": 0.0, "qty": 0.0},  # level 0
    ]

    days = (
        CalendarGrid.build(1999, daily_data=daily, today=date(1999, 12, 31))
        .months[0]
        .days
    )

    qty_str = _("Quantity")
    gap_str = _("Gap")
    assert [d.level for d in days[:5]] == [1, 2, 3, 4, 0]
    assert days[0].label == f"1999-01-01\n{qty_str}: 0.4\n{gap_str}: 0d."
    assert days[3].label == f"1999-01-04\n{qty_str}: 2.4\n{gap_str}: 1d."
    assert days[4].label == ""
    assert days[0].gap == 0
    assert days[3].gap == 1


def test_build_gaps_with_latest_past_date():
    daily = [
        {"date": date(1999, 1, 10), "stdav": 1.0, "qty": 0.5},
        {"date": date(1999, 1, 15), "stdav": 2.0, "qty": 1.0},
    ]
    grid = CalendarGrid.build(
        1999,
        daily_data=daily,
        latest_past_date=date(1999, 1, 5),
        today=date(1999, 12, 31),
    )

    jan_days = grid.months[0].days
    day_10 = jan_days[9]
    day_15 = jan_days[14]

    qty_str = _("Quantity")
    gap_str = _("Gap")
    assert day_10.gap == 5
    assert day_10.label == f"1999-01-10\n{qty_str}: 0.5\n{gap_str}: 5d."
    assert day_15.gap == 5
    assert day_15.label == f"1999-01-15\n{qty_str}: 1.0\n{gap_str}: 5d."


def test_build_today_and_future_flags():
    grid = CalendarGrid.build(1999, daily_data=[], today=date(1999, 6, 15))

    june = grid.months[5].days
    assert june[14].is_today is True  # 15th
    assert june[14].is_future is False
    assert june[15].is_future is True  # 16th
    # a past month has no future days
    assert all(not d.is_future for d in grid.months[0].days)


def test_build_today_without_record_shows_date_and_gap():
    daily = [{"date": date(1999, 6, 5), "stdav": 1.0, "qty": 0.5}]
    grid = CalendarGrid.build(1999, daily_data=daily, today=date(1999, 6, 15))

    june_days = grid.months[5].days
    today_day = june_days[14]  # 15th

    gap_str = _("Gap")
    assert today_day.is_today is True
    assert today_day.level == 0
    assert today_day.gap == 10
    assert today_day.label == f"1999-06-15\n{gap_str}: 10d."


def test_build_today_without_record_uses_latest_past_date():
    grid = CalendarGrid.build(
        1999,
        daily_data=[],
        latest_past_date=date(1998, 12, 1),
        today=date(1999, 1, 10),
    )

    jan_days = grid.months[0].days
    today_day = jan_days[9]  # 10th

    gap_str = _("Gap")
    assert today_day.is_today is True
    assert today_day.level == 0
    assert today_day.gap == 40
    assert today_day.label == f"1999-01-10\n{gap_str}: 40d."


def test_build_other_year_has_no_future_days():
    grid = CalendarGrid.build(1998, daily_data=[], today=date(1999, 6, 15))

    assert all(not d.is_future for m in grid.months for d in m.days)


def test_build_a_year_not_started_yet_has_no_future_days():
    # next year is selectable and none of it is flagged future - long-standing
    # behaviour, pinned because the flag now reads off the year boundary
    grid = CalendarGrid.build(2000, daily_data=[], today=date(1999, 6, 15))

    assert all(not d.is_future for m in grid.months for d in m.days)
