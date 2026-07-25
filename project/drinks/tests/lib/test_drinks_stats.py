from datetime import date

import pytest

from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DataRow, DrinkStats

pytestmark = pytest.mark.django_db


@pytest.fixture(name="drink_converter")
def fixture_drink_converter():
    return DrinkConverter("beer")


@pytest.mark.parametrize(
    "drink_type, stdav, qty, expect_qty, expect_vol",
    [
        (
            "beer",
            2.5,
            1,
            [1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [500.0, 1000.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ),
        (
            "wine",
            8,
            1,
            [1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [750.0, 1500.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ),
    ],
)
def test_monthly_stats(drink_type, stdav, qty, expect_qty, expect_vol):
    data = [
        DataRow(date=date(1999, 1, 1), qty=qty, stdav=stdav),
        DataRow(date=date(1999, 2, 1), qty=qty * 2, stdav=stdav * 2),
    ]

    converter = DrinkConverter(drink_type)
    obj = DrinkStats(converter, data)
    stats = obj.monthly

    assert stats.total_quantity == expect_qty
    assert stats.total_volume_ml == expect_vol
    assert len(stats.avg_daily_volume_ml) == 12


def test_monthly_stats_no_data(drink_converter):
    obj = DrinkStats(drink_converter)
    stats = obj.monthly

    assert stats.total_quantity == [0.0] * 12
    assert stats.total_volume_ml == [0.0] * 12
    assert stats.avg_daily_volume_ml == [0.0] * 12


@pytest.mark.parametrize(
    "year, today, expect_avg_volume, expect_total_qty",
    [
        (1999, date(1999, 1, 1), 500.0, 1.0),  # First day of year
        (1999, date(1999, 1, 31), 16.13, 1.0),  # End of January
        (1999, date(1999, 12, 31), 2.74, 2.0),  # End of year
        (1999, date(2000, 1, 1), 2.74, 2.0),  # Next year (past year)
        (2000, date(2000, 12, 31), 2.73, 2.0),  # Leap year (366 days)
    ],
)
def test_yearly_stats(year, today, expect_avg_volume, expect_total_qty):
    data = [
        DataRow(date=date(year, 1, 1), qty=1, stdav=2.5),
        DataRow(date=date(year, 2, 1), qty=1, stdav=2.5),
    ]

    converter = DrinkConverter("beer")
    obj = DrinkStats(converter, data, today=today)
    stats = obj.yearly

    assert round(stats.avg_daily_volume_ml, 2) == expect_avg_volume
    assert stats.total_quantity == expect_total_qty


def test_yearly_stats_no_data(drink_converter):
    obj = DrinkStats(drink_converter)
    stats = obj.yearly

    assert stats.avg_daily_volume_ml == 0.0
    assert stats.avg_daily_stdav == 0.0
    assert stats.total_quantity == 0.0
    assert stats.stdav == 0.0
    assert stats.pure_alcohol_liters == 0.0


def test_yearly_stats_pure_alcohol(drink_converter):
    data = [DataRow(date=date(1999, 1, 1), qty=1, stdav=2.5)]

    obj = DrinkStats(drink_converter, data, today=date(1999, 12, 31))

    assert obj.yearly.stdav == 2.5
    assert obj.yearly.pure_alcohol_liters == 0.025


def test_year_falls_back_to_today_when_empty(drink_converter):
    obj = DrinkStats(drink_converter, today=date(2005, 3, 1))

    assert obj.year == 2005


def test_year_comes_from_the_data(drink_converter):
    data = [DataRow(date=date(1999, 1, 1), qty=1, stdav=2.5)]

    obj = DrinkStats(drink_converter, data, today=date(2005, 3, 1))

    assert obj.year == 1999
