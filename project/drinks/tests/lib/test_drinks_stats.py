from datetime import date

import pytest
import time_machine

from ...lib.drinks_options import DrinksOptions
from ...lib.drinks_stats import DrinkStats

pytestmark = pytest.mark.django_db


@pytest.fixture(name="drinks_options")
def fixture_drinks_options():
    return DrinksOptions("beer")


@pytest.fixture(name="set_drink_type")
def fixture_set_drink_type(drinks_options):
    def _set(drink_type):
        drinks_options.drink_type = drink_type
        return drinks_options

    return _set


@pytest.mark.parametrize(
    "drink_type, stdav, qty, expect",
    [
        ("beer", 2.5, 1, [1, 2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("wine", 8, 1, [1, 2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("vodka", 40, 1, [1, 2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("stdav", 1, 1, [1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ],
)
@time_machine.travel("1999-12-01")
def test_qty_of_month(drink_type, stdav, qty, expect, set_drink_type):
    data = [
        {"date": date(1999, 1, 1), "qty": qty, "stdav": stdav},
        {"date": date(1999, 2, 1), "qty": qty * 2, "stdav": stdav * 2},
    ]

    options = set_drink_type(drink_type)
    obj = DrinkStats(options, data)
    actual = obj.qty_of_month

    assert actual == expect
    assert obj.options.drink_type == drink_type


@pytest.mark.parametrize(
    "drink_type, expect",
    [
        ("beer", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("wine", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("vodka", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("stdav", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ],
)
@time_machine.travel("1999-12-01")
def test_qty_of_month_no_data(drink_type, expect, set_drink_type):
    data = []

    options = set_drink_type(drink_type)
    obj = DrinkStats(options, data)
    actual = obj.qty_of_month

    assert actual == expect
    assert obj.options.drink_type == drink_type


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        (
            "beer",
            1,
            2.5,
            [16.13, 35.71, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ),
        (
            "wine",
            1,
            8,
            [24.19, 53.57, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ),
        (
            "vodka",
            1,
            40,
            [32.23, 71.43, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ),
        ("stdav", 1, 1, [0.32, 0.71, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ],
)
@time_machine.travel("1999-12-01")
def test_per_day_of_month(drink_type, qty, stdav, expect, set_drink_type):
    data = [
        {"date": date(1999, 1, 1), "qty": qty, "stdav": stdav},
        {"date": date(1999, 2, 1), "qty": qty * 2, "stdav": stdav * 2},
    ]

    options = set_drink_type(drink_type)
    actual = DrinkStats(options, data).per_day_of_month

    assert pytest.approx(actual, 0.01) == expect


@pytest.mark.parametrize(
    "drink_type, expect",
    [
        ("beer", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("wine", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("vodka", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("stdav", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ],
)
@time_machine.travel("1999-12-01")
def test_per_day_of_month_no_data(drink_type, expect, set_drink_type):
    data = []

    options = set_drink_type(drink_type)
    actual = DrinkStats(options, data).per_day_of_month

    assert actual == expect


@time_machine.travel("1999-1-1")
def test_qty_of_year(drinks_options):
    data = [
        {"date": date(1999, 1, 1), "qty": 1, "stdav": 2.5},
        {"date": date(1999, 2, 1), "qty": 1, "stdav": 2.5},
    ]

    actual = DrinkStats(drinks_options, data).qty_of_year

    assert actual == 2.0


@time_machine.travel("1999-1-1")
def test_per_month(drinks_options):
    data = [
        {"date": date(1999, 1, 1), "qty": 1, "stdav": 2.5},
        {"date": date(1999, 2, 1), "qty": 2, "stdav": 5.0},
    ]

    actual = DrinkStats(drinks_options, data).per_month

    assert actual == [500.0, 1000.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


@pytest.mark.parametrize(
    "dt, expect",
    [
        ("1999-1-1", 500),
        ("1999-1-31", 16.13),
        ("1999-2-1", 31.25),
        ("1999-12-31", 2.74),
        ("2000-1-1", 2.74),
    ],
)
def test_per_day_of_year(dt, expect, drinks_options):
    with time_machine.travel(dt):
        data = [
            {"date": date(1999, 1, 1), "qty": 1, "stdav": 2.5},
            {"date": date(1999, 2, 1), "qty": 1, "stdav": 2.5},
        ]

        actual = DrinkStats(drinks_options, data).per_day_of_year

        assert round(actual, 2) == expect
