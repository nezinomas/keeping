from datetime import date

import pytest

from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import (
    DataRow,
    DrinkStats,
    EmptyYearOverYear,
    YearOverYear,
)

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
    assert stats.total_volume == expect_vol
    assert len(stats.avg_daily_volume) == 12


def test_monthly_stats_no_data(drink_converter):
    obj = DrinkStats(drink_converter, today=date(1999, 12, 31))
    stats = obj.monthly

    assert stats.total_quantity == [0.0] * 12
    assert stats.total_volume == [0.0] * 12
    assert stats.avg_daily_volume == [0.0] * 12


def test_monthly_stats_stop_at_the_year_boundary():
    data = [DataRow(date=date(1999, 1, 1), qty=1, stdav=2.5)]

    stats = DrinkStats(DrinkConverter("beer"), data, today=date(1999, 8, 9)).monthly

    assert stats.avg_daily_volume[7] == 0.0  # August has begun
    assert stats.avg_daily_volume[8:] == [None] * 4
    assert stats.total_quantity[8:] == [None] * 4
    assert stats.total_volume[8:] == [None] * 4


def test_monthly_stats_run_to_december_once_the_year_is_over():
    data = [DataRow(date=date(1999, 1, 1), qty=1, stdav=2.5)]

    stats = DrinkStats(DrinkConverter("beer"), data, today=date(2005, 3, 1)).monthly

    assert None not in stats.avg_daily_volume
    assert None not in stats.total_quantity
    assert None not in stats.total_volume


def test_monthly_stats_carry_the_std_av_they_summed():
    data = [DataRow(date=date(1999, 1, 1), qty=1, stdav=2.5)]

    stats = DrinkStats(DrinkConverter("beer"), data, today=date(1999, 12, 31)).monthly

    assert stats.total_stdav[0] == 2.5
    assert stats.total_stdav[1] == 0.0


def test_yearly_std_av_is_summed_not_rebuilt_from_the_shown_quantity():
    data = [DataRow(date=date(1999, 1, 1), qty=0.1 * 0.4, stdav=0.1)]

    stats = DrinkStats(DrinkConverter("beer"), data, today=date(1999, 12, 31)).yearly

    assert stats.stdav == 0.1


def test_yearly_stats_ignore_the_months_past_the_boundary():
    data = [DataRow(date=date(1999, 1, 1), qty=1, stdav=2.5)]

    stats = DrinkStats(DrinkConverter("beer"), data, today=date(1999, 8, 9)).yearly

    assert stats.total_quantity == 1.0
    assert stats.stdav == 2.5


def test_monthly_stats_shows_std_av_as_typed():
    """Std Av is canonical, so it is shown as typed — not as the ml in it.

    Converting would put the Overview chart 10x above the Drink Target drawn
    across it, the way the Trends chart used to be.
    """
    data = [DataRow(date=date(1999, 1, 1), qty=5, stdav=5)]

    stats = DrinkStats(DrinkConverter("stdav"), data).monthly

    assert stats.total_volume[0] == 5.0
    assert stats.avg_daily_volume[0] == pytest.approx(5 / 31)


def test_yearly_stats_shows_std_av_as_typed():
    data = [DataRow(date=date(1999, 1, 1), qty=5, stdav=5)]

    stats = DrinkStats(DrinkConverter("stdav"), data, today=date(1999, 1, 1)).yearly

    assert stats.avg_daily_volume == 5.0


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

    assert round(stats.avg_daily_volume, 2) == expect_avg_volume
    assert stats.total_quantity == expect_total_qty


def test_yearly_stats_no_data(drink_converter):
    obj = DrinkStats(drink_converter)
    stats = obj.yearly

    assert stats.avg_daily_volume == 0.0
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


# -------------------------------------------------------------------------------------
#                                                                        YearOverYear
# -------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "current, previous, expect",
    [(1.0, 2.0, True), (2.0, 1.0, False), (2.0, 2.0, True)],
)
def test_a_year_equal_to_the_last_one_crosses_nothing(current, previous, expect):
    """Harm means a threshold was crossed, and last year's own figure is not
    above itself."""
    assert YearOverYear(current, previous).improving is expect


def test_a_year_read_against_a_past_one_says_it_has_one():
    assert YearOverYear(1.0, 2.0).has_past is True


def test_without_a_past_year_only_the_current_figure_is_read():
    empty = EmptyYearOverYear(3.0)

    assert empty.has_past is False
    assert empty.current == 3.0
    assert empty.previous == 0.0
    assert empty.improving is False


@pytest.mark.parametrize("field", ["improving", "has_past"])
def test_a_comparison_cannot_be_given_a_direction_it_did_not_derive(field):
    """The two figures are the direction, so a second answer could contradict
    them."""
    with pytest.raises(TypeError):
        YearOverYear(1.0, 2.0, **{field: True})


@pytest.mark.parametrize("field", ["previous", "improving", "has_past"])
def test_an_empty_comparison_cannot_be_given_a_past_year(field):
    with pytest.raises(TypeError):
        EmptyYearOverYear(3.0, **{field: 1.0})


@pytest.mark.parametrize("reading", [YearOverYear(1.0, 2.0), EmptyYearOverYear(3.0)])
def test_every_comparison_answers_what_a_card_reads(reading):
    for name in ("current", "previous", "improving", "has_past"):
        assert hasattr(reading, name), name
