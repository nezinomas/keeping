import pytest
import time_machine

from ..services import history

pytestmark = pytest.mark.django_db


@time_machine.travel("1999-01-01")
def test_insert_empty_values():
    data = [{"year": 1998, "qty": 1, "stdav": 2.5}]
    actual = history.HistoryService.insert_empty_values(data)
    expect = [
        {"year": 1998, "qty": 1, "stdav": 2.5},
        {"year": 1998, "qty": 0, "stdav": 0.0},
        {"year": 1999, "qty": 0, "stdav": 0.0},
    ]
    assert actual == expect


@time_machine.travel("2000-01-01")
def test_years():
    qs = [{"year": 1998, "qty": 1, "stdav": 2.5}]
    actual = history.HistoryService(qs).years

    assert actual == [1998, 1999, 2000]


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 1, 2.5, [0.025, 0.0]),
        ("wine", 1, 8, [0.08, 0.0]),
        ("vodka", 1, 40, [0.4, 0.0]),
        ("stdav", 1, 10, [0.1, 0.0]),
    ],
)
@time_machine.travel("2000-01-01")
def test_pure_alcohol(drink_type, qty, stdav, expect, main_user):
    main_user.drink_type = drink_type

    qs = [{"year": 1999, "qty": qty, "stdav": stdav}]

    actual = history.HistoryService(qs).alcohol

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 365, 912.5, [500.0, 0.0]),
        ("wine", 365, 2_920, [750.0, 0.0]),
        ("vodka", 365, 14_600, [1000.0, 0.0]),
        ("stdav", 365, 365, [10.0, 0.0]),
    ],
)
@time_machine.travel("2000-01-01")
def test_per_day(drink_type, qty, stdav, expect, main_user):
    main_user.drink_type = drink_type

    qs = [{"year": 1999, "qty": qty, "stdav": stdav}]

    actual = history.HistoryService(qs).per_day

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 365, 912.5, [500.0, 182_500]),
        ("wine", 365, 2_920, [750.0, 273_750]),
        ("vodka", 365, 14_600, [1000.0, 365_000]),
        ("stdav", 365, 365, [10.0, 3_650]),
    ],
)
@time_machine.travel("2000-01-01")
def test_per_day_adjusted_for_current_year(drink_type, qty, stdav, expect, main_user):
    main_user.drink_type = drink_type

    qs = [
        {"year": 1999, "qty": qty, "stdav": stdav},
        {"year": 2000, "qty": qty, "stdav": stdav},
    ]

    actual = history.HistoryService(qs).per_day

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 365, 912.5, [365.0, 0.0]),
        ("wine", 365, 2_920, [365.0, 0.0]),
        ("vodka", 365, 14_600, [365.0, 0.0]),
        ("stdav", 365, 365, [365.0, 0.0]),
    ],
)
@time_machine.travel("2000-01-01")
def test_quantity(drink_type, qty, stdav, expect, main_user):
    main_user.drink_type = drink_type

    qs = [{"year": 1999, "qty": qty, "stdav": stdav}]

    actual = history.HistoryService(qs).quantity

    assert actual == expect
