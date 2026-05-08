from datetime import date

import pytest
import time_machine

from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DrinkStats

pytestmark = pytest.mark.django_db


@pytest.fixture(name="drink_converter")
def fixture_drink_converter():
    return DrinkConverter("beer")


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
def test_qty_of_month(drink_type, stdav, qty, expect):
    data = [
        {"date": date(1999, 1, 1), "qty": qty, "stdav": stdav},
        {"date": date(1999, 2, 1), "qty": qty * 2, "stdav": stdav * 2},
    ]

    converter = DrinkConverter(drink_type)
    obj = DrinkStats(converter, data)

    assert obj.monthly.total_quantity == expect
    assert obj.converter.drink_type == drink_type


@time_machine.travel("1999-12-01")
def test_qty_of_month_no_data(drink_converter):
    obj = DrinkStats(drink_converter, [])

    assert obj.monthly.total_quantity == [0.0] * 12


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
def test_per_day_of_month(drink_type, qty, stdav, expect):
    data = [
        {"date": date(1999, 1, 1), "qty": qty, "stdav": stdav},
        {"date": date(1999, 2, 1), "qty": qty * 2, "stdav": stdav * 2},
    ]

    actual = DrinkStats(DrinkConverter(drink_type), data).monthly.avg_daily_volume_ml

    assert pytest.approx(actual, 0.01) == expect


@time_machine.travel("1999-12-01")
def test_per_day_of_month_no_data(drink_converter):
    actual = DrinkStats(drink_converter, []).monthly.avg_daily_volume_ml

    assert actual == [0.0] * 12


@time_machine.travel("1999-1-1")
def test_qty_of_year(drink_converter):
    data = [
        {"date": date(1999, 1, 1), "qty": 1, "stdav": 2.5},
        {"date": date(1999, 2, 1), "qty": 1, "stdav": 2.5},
    ]

    actual = DrinkStats(drink_converter, data).yearly.total_quantity

    assert actual == 2.0


@time_machine.travel("1999-1-1")
def test_per_month(drink_converter):
    data = [
        {"date": date(1999, 1, 1), "qty": 1, "stdav": 2.5},
        {"date": date(1999, 2, 1), "qty": 2, "stdav": 5.0},
    ]

    actual = DrinkStats(drink_converter, data).monthly.total_volume_ml

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
def test_per_day_of_year(dt, expect, drink_converter):
    with time_machine.travel(dt):
        data = [
            {"date": date(1999, 1, 1), "qty": 1, "stdav": 2.5},
            {"date": date(1999, 2, 1), "qty": 1, "stdav": 2.5},
        ]

        actual = DrinkStats(drink_converter, data).yearly.avg_daily_volume_ml

        assert round(actual, 2) == expect
