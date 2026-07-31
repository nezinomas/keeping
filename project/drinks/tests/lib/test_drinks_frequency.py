from datetime import date

import pytest
import time_machine

from ...lib.drinks_frequency import FrequencyStats
from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DataRow


def _row(dt: date, stdav: float, qty: float = 0.0) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=qty)


# -------------------------------------------------------------------------------------
#                                                                          current_year
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-06-15")
def test_current_year_defaults_to_today_with_no_arguments():
    assert FrequencyStats().current_year == 2026


@time_machine.travel("2026-06-15")
def test_current_year_taken_from_records():
    stats = FrequencyStats(current_daily=[_row(date(2025, 3, 1), 5)])
    assert stats.current_year == 2025


# -------------------------------------------------------------------------------------
#                                                                         drinking_days
# -------------------------------------------------------------------------------------
def test_drinking_days_counts_distinct_dates_not_rows():
    rows = [
        _row(date(2025, 1, 5), 3),
        _row(date(2025, 1, 5), 4),  # same day, second record
        _row(date(2025, 1, 6), 2),
    ]

    assert FrequencyStats(current_daily=rows, today=date(2025, 6, 1)).drinking_days == 2


def test_drinking_days_no_records_is_zero():
    assert FrequencyStats(today=date(2025, 6, 1)).drinking_days == 0


def test_drinking_days_counts_the_last_day_of_the_year():
    rows = [_row(date(2025, 12, 31), 5)]

    assert FrequencyStats(current_daily=rows, today=date(2026, 6, 1)).drinking_days == 1


# -------------------------------------------------------------------------------------
#                                                                              dry_days
# -------------------------------------------------------------------------------------
def test_dry_days_past_year_uses_the_whole_year():
    rows = [_row(date(2025, 1, 5), 3), _row(date(2025, 1, 6), 3)]
    stats = FrequencyStats(current_daily=rows, today=date(2026, 6, 15))

    assert stats.dry_days == 365 - 2


def test_dry_days_past_leap_year_uses_366():
    rows = [_row(date(2024, 1, 5), 3)]
    stats = FrequencyStats(current_daily=rows, today=date(2026, 6, 15))

    assert stats.dry_days == 366 - 1


def test_dry_days_current_year_uses_day_of_year():
    rows = [_row(date(2026, 1, 5), 3), _row(date(2026, 2, 6), 3)]
    stats = FrequencyStats(current_daily=rows, today=date(2026, 1, 10))

    assert stats.dry_days == 10 - 2


def test_dry_days_never_negative():
    rows = [_row(date(2026, 1, i), 3) for i in range(1, 11)]
    stats = FrequencyStats(current_daily=rows, today=date(2026, 1, 5))

    assert stats.dry_days == 0


# -------------------------------------------------------------------------------------
#                                                        dry_share / drinking_day_share
# -------------------------------------------------------------------------------------
def test_shares_split_the_days_elapsed():
    rows = [_row(date(2026, 1, i), 3) for i in range(1, 5)]
    stats = FrequencyStats(current_daily=rows, today=date(2026, 1, 10))

    assert stats.drinking_day_share == 0.4
    assert stats.dry_share == 0.6


def test_shares_on_an_empty_year_are_zero():
    stats = FrequencyStats(today=date(2026, 6, 15))

    assert stats.dry_share == 0.0
    assert stats.drinking_day_share == 0.0


# -------------------------------------------------------------------------------------
#                                                                             intensity
# -------------------------------------------------------------------------------------
def test_intensity_is_total_over_drinking_days():
    rows = [_row(date(2026, 1, 5), 7), _row(date(2026, 1, 8), 3)]
    stats = FrequencyStats(current_daily=rows, today=date(2026, 6, 15))

    assert stats.intensity == 5.0


def test_intensity_divides_by_drinking_days_not_rows():
    rows = [
        _row(date(2026, 1, 5), 4),
        _row(date(2026, 1, 5), 6),
        _row(date(2026, 1, 8), 2),
    ]
    stats = FrequencyStats(current_daily=rows, today=date(2026, 6, 15))

    assert stats.intensity == 6.0


def test_intensity_with_no_records_is_zero():
    assert FrequencyStats(today=date(2026, 6, 15)).intensity == 0.0


def test_intensity_is_unchanged_by_the_order_of_the_days():
    days = [date(2026, 1, 5), date(2026, 2, 9), date(2026, 3, 14)]
    amounts = [2.0, 5.5, 8.0]
    forward = [_row(d, a) for d, a in zip(days, amounts)]
    shuffled = [
        _row(days[2], amounts[1]),
        _row(days[0], amounts[2]),
        _row(days[1], amounts[0]),
    ]

    today = date(2026, 6, 15)
    assert (
        FrequencyStats(current_daily=forward, today=today).intensity
        == FrequencyStats(current_daily=shuffled, today=today).intensity
    )


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
def test_intensity_is_the_same_figure_under_every_drink_type(drink_type):
    # qty is the drink-type reading of the same Std Av; intensity is a harm
    # metric and must never be computed from it
    ratio = DrinkConverter(drink_type).ratio
    rows = [
        _row(date(2026, 1, 5), 7, qty=7 * ratio),
        _row(date(2026, 1, 8), 3, qty=3 * ratio),
    ]

    stats = FrequencyStats(current_daily=rows, today=date(2026, 6, 15))

    assert stats.intensity == 5.0


# -------------------------------------------------------------------------------------
#                                                                    compare_frequency
# -------------------------------------------------------------------------------------
def test_compare_frequency_counts_both_years():
    current = [_row(date(2026, 1, 5), 3), _row(date(2026, 1, 6), 3)]
    past = [_row(date(2025, 1, 5), 3)]

    actual = FrequencyStats(current, past, today=date(2026, 6, 15)).compare_frequency()

    assert actual.current == 2
    assert actual.previous == 1
    assert actual.has_past is True
    assert actual.improving is False


def test_compare_frequency_fewer_days_is_improving():
    current = [_row(date(2026, 1, 5), 3)]
    past = [_row(date(2025, 1, 5), 3), _row(date(2025, 1, 6), 3)]

    actual = FrequencyStats(current, past, today=date(2026, 6, 15)).compare_frequency()

    assert actual.improving is True


def test_compare_frequency_without_a_prior_year_is_empty():
    current = [_row(date(2026, 1, 5), 3)]

    actual = FrequencyStats(current, today=date(2026, 6, 15)).compare_frequency()

    assert actual.current == 1
    assert actual.previous == 0
    assert actual.has_past is False
    assert actual.improving is False


def test_compare_frequency_clips_the_prior_year_on_month_and_day():
    current = [_row(date(2026, 1, 5), 3)]
    past = [
        _row(date(2025, 1, 5), 3),  # before the cutoff
        _row(date(2025, 3, 1), 3),  # the cutoff itself
        _row(date(2025, 6, 20), 3),  # after it
    ]

    actual = FrequencyStats(current, past, today=date(2026, 3, 1)).compare_frequency()

    assert actual.previous == 2


def test_compare_frequency_clips_a_leap_day_in_the_prior_year():
    current = [_row(date(2025, 1, 5), 3)]
    past = [
        _row(date(2024, 2, 29), 3),  # kept: 02-29 <= 03-01
        _row(date(2024, 3, 2), 3),  # dropped
    ]

    actual = FrequencyStats(current, past, today=date(2025, 3, 1)).compare_frequency()

    assert actual.previous == 1


def test_compare_frequency_clips_the_prior_year_of_a_leap_year():
    current = [_row(date(2024, 1, 5), 3)]
    past = [
        _row(date(2023, 2, 28), 3),  # kept
        _row(date(2023, 3, 5), 3),  # dropped
    ]

    actual = FrequencyStats(current, past, today=date(2024, 2, 29)).compare_frequency()

    assert actual.previous == 1


# -------------------------------------------------------------------------------------
#                                                                    compare_intensity
# -------------------------------------------------------------------------------------
def test_compare_intensity_reads_both_years_per_drinking_day():
    current = [_row(date(2026, 1, 5), 8), _row(date(2026, 1, 6), 4)]
    past = [_row(date(2025, 1, 5), 4), _row(date(2025, 1, 6), 4)]

    actual = FrequencyStats(current, past, today=date(2026, 6, 15)).compare_intensity()

    assert actual.current == 6.0
    assert actual.previous == 4.0
    assert actual.improving is False


def test_compare_intensity_less_per_day_is_improving():
    current = [_row(date(2026, 1, 5), 2)]
    past = [_row(date(2025, 1, 5), 9)]

    actual = FrequencyStats(current, past, today=date(2026, 6, 15)).compare_intensity()

    assert actual.improving is True


def test_compare_intensity_clips_the_prior_year_on_month_and_day():
    current = [_row(date(2026, 1, 5), 5)]
    past = [
        _row(date(2025, 1, 5), 3),
        _row(date(2025, 9, 9), 99),  # after the cutoff, must not raise the average
    ]

    actual = FrequencyStats(current, past, today=date(2026, 3, 1)).compare_intensity()

    assert actual.previous == 3.0


def test_compare_intensity_without_a_prior_year_is_empty():
    current = [_row(date(2026, 1, 5), 5)]

    actual = FrequencyStats(current, today=date(2026, 6, 15)).compare_intensity()

    assert actual.current == 5.0
    assert actual.previous == 0.0
    assert actual.has_past is False


def test_compare_intensity_on_no_data_is_empty_and_does_not_raise():
    actual = FrequencyStats(today=date(2026, 6, 15)).compare_intensity()

    assert actual.current == 0.0
    assert actual.has_past is False


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
def test_compare_intensity_is_the_same_figure_under_every_drink_type(drink_type):
    ratio = DrinkConverter(drink_type).ratio
    current = [_row(date(2026, 1, 5), 6, qty=6 * ratio)]
    past = [_row(date(2025, 1, 5), 4, qty=4 * ratio)]

    actual = FrequencyStats(current, past, today=date(2026, 6, 15)).compare_intensity()

    assert actual.current == 6.0
    assert actual.previous == 4.0


# -------------------------------------------------------------------------------------
#                                                        the empty variants' field surface
# -------------------------------------------------------------------------------------
def test_empty_comparison_exposes_the_same_fields_as_the_populated_one():
    populated = FrequencyStats(
        [_row(date(2026, 1, 5), 3)],
        [_row(date(2025, 1, 5), 3)],
        today=date(2026, 6, 15),
    ).compare_frequency()
    empty = FrequencyStats(today=date(2026, 6, 15)).compare_frequency()

    assert {f for f in vars(populated)} == {f for f in vars(empty)}
