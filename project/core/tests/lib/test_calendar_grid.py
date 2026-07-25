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
