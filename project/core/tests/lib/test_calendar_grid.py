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

THRESHOLDS = (2.0, 4.0, 6.0)


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
    grid = CalendarGrid.build(
        1999,
        daily_data=daily,
        today=date(1999, 12, 31),
        thresholds=THRESHOLDS,
        value_key="stdav",
    )

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
    assert all(d.label == "" for m in grid.months for d in m.days if d.is_future)
    gap_str = _("Gap")
    assert grid.months[5].days[14].label == f"1999-06-15\n{gap_str}: 0d."


def test_build_month_metadata():
    grid = CalendarGrid.build(1999, daily_data=[], today=date(1999, 12, 31))

    jan = grid.months[0]
    assert jan.number == 1
    assert len(jan.days) == 31
    assert jan.leading_blanks == date(1999, 1, 1).weekday()

    feb = grid.months[1]
    assert feb.number == 2
    assert len(feb.days) == 28
    assert feb.leading_blanks == date(1999, 2, 1).weekday()


def test_build_all_levels_and_labels():
    daily = [
        {"date": date(1999, 1, 1), "stdav": 1.0, "qty": 0.4},
        {"date": date(1999, 1, 2), "stdav": 2.0, "qty": 0.8},
        {"date": date(1999, 1, 3), "stdav": 4.0, "qty": 1.6},
        {"date": date(1999, 1, 4), "stdav": 6.0, "qty": 2.4},
        {"date": date(1999, 1, 5), "stdav": 0.0, "qty": 0.0},
    ]

    days = (
        CalendarGrid.build(
            1999,
            daily_data=daily,
            today=date(1999, 12, 31),
            thresholds=THRESHOLDS,
            value_key="stdav",
            empty_title=_("No drink"),
        )
        .months[0]
        .days
    )

    qty_str = _("Quantity")
    gap_str = _("Gap")
    assert [d.level for d in days[:5]] == [1, 2, 3, 4, 0]
    assert days[0].label == f"1999-01-01\n{qty_str}: 0.4\n{gap_str}: 0d."
    assert days[3].label == f"1999-01-04\n{qty_str}: 2.4\n{gap_str}: 1d."
    assert days[4].label == f"1999-01-05\n{_('No drink')}"
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
    assert june[14].is_today is True
    assert june[14].is_future is False
    assert june[15].is_future is True
    assert all(not d.is_future for d in grid.months[0].days)


def test_build_today_without_record_shows_date_and_gap():
    daily = [{"date": date(1999, 6, 5), "stdav": 1.0, "qty": 0.5}]
    grid = CalendarGrid.build(1999, daily_data=daily, today=date(1999, 6, 15))

    june_days = grid.months[5].days
    today_day = june_days[14]

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
    today_day = jan_days[9]

    gap_str = _("Gap")
    assert today_day.is_today is True
    assert today_day.level == 0
    assert today_day.gap == 40
    assert today_day.label == f"1999-01-10\n{gap_str}: 40d."


def test_build_other_year_has_no_future_days():
    grid = CalendarGrid.build(1998, daily_data=[], today=date(1999, 6, 15))

    assert all(not d.is_future for m in grid.months for d in m.days)


def test_a_dry_day_is_labelled_rather_than_left_blank():
    grid = CalendarGrid.build(
        1999, daily_data=[], today=date(1999, 12, 31), empty_title=_("No drink")
    )

    assert grid.months[0].days[0].label == f"1999-01-01\n{_('No drink')}"


def test_an_empty_day_with_no_word_for_empty_is_labelled_with_its_date_alone():
    grid = CalendarGrid.build(1999, daily_data=[], today=date(1999, 12, 31))

    assert grid.months[0].days[0].label == "1999-01-01"


def test_a_future_day_carries_no_label():
    grid = CalendarGrid.build(1999, daily_data=[], today=date(1999, 6, 15))

    assert grid.months[5].days[15].label == ""


def test_a_days_speech_is_its_label_on_one_line():
    daily = [{"date": date(1999, 1, 1), "stdav": 1.0, "qty": 0.4}]
    grid = CalendarGrid.build(1999, daily_data=daily, today=date(1999, 12, 31))

    qty_str = _("Quantity")
    gap_str = _("Gap")
    assert grid.months[0].days[0].speech == (
        f"1999-01-01, {qty_str}: 0.4, {gap_str}: 0d."
    )


def test_legend_bounds_name_every_level():
    grid = CalendarGrid.build(
        1999, daily_data=[], today=date(1999, 12, 31), thresholds=THRESHOLDS
    )

    assert grid.legend.bounds == ("0", "<2", "2-4", "4-6", ">=6")


def test_without_thresholds_the_legend_has_two_steps():
    grid = CalendarGrid.build(1999, daily_data=[], today=date(1999, 12, 31))

    assert grid.legend.bounds == ("0", ">0")


def test_legend_carries_the_words_at_either_end_of_the_scale():
    grid = CalendarGrid.build(
        1999,
        daily_data=[],
        today=date(1999, 12, 31),
        low_title="nothing",
        high_title="plenty",
    )

    assert grid.legend.low_title == "nothing"
    assert grid.legend.high_title == "plenty"


def test_legend_carries_the_unit_the_levels_are_read_in():
    grid = CalendarGrid.build(
        1999, daily_data=[], today=date(1999, 12, 31), unit="Std Av"
    )

    assert grid.legend.unit == "Std Av"


def test_without_thresholds_every_day_with_a_value_is_one_level():
    daily = [
        {"date": date(1999, 1, 1), "qty": 0.1},
        {"date": date(1999, 1, 2), "qty": 99.0},
        {"date": date(1999, 1, 3), "qty": 0.0},
    ]
    grid = CalendarGrid.build(1999, daily_data=daily, today=date(1999, 12, 31))

    assert [d.level for d in grid.months[0].days[:3]] == [1, 1, 0]


def test_build_a_year_not_started_yet_has_no_future_days():
    grid = CalendarGrid.build(2000, daily_data=[], today=date(1999, 6, 15))

    assert all(not d.is_future for m in grid.months for d in m.days)
