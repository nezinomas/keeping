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


def test_is_current_year_while_the_year_runs():
    rows = [_row(date(2026, 1, 5), 3)]

    assert FrequencyStats(current_daily=rows, today=date(2026, 6, 15)).is_current_year


def test_is_current_year_is_false_once_the_year_is_over():
    rows = [_row(date(2025, 1, 5), 3)]

    assert not FrequencyStats(
        current_daily=rows, today=date(2026, 6, 15)
    ).is_current_year


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
#                                                                      weekday_profile
# -------------------------------------------------------------------------------------
def test_weekday_profile_is_always_seven_points_monday_first():
    actual = FrequencyStats(today=date(2026, 6, 15)).weekday_profile()

    assert [point.weekday for point in actual] == [0, 1, 2, 3, 4, 5, 6]


def test_weekday_profile_puts_a_monday_drink_at_index_zero():
    # 2026-06-15 is a Monday, and the test says so rather than trusting it
    monday = date(2026, 6, 15)
    assert monday.weekday() == 0

    actual = FrequencyStats([_row(monday, 5)], today=monday).weekday_profile()

    assert actual[0].drinking_days == 1
    assert [point.drinking_days for point in actual[1:]] == [0] * 6


def test_weekday_profile_puts_a_sunday_drink_at_index_six():
    # 2026-06-21 is a Sunday — the last index, since the week starts on Monday
    sunday = date(2026, 6, 21)
    assert sunday.weekday() == 6

    actual = FrequencyStats([_row(sunday, 5)], today=sunday).weekday_profile()

    assert actual[6].drinking_days == 1


def test_weekday_profile_counts_only_the_weekdays_elapsed_in_a_running_year():
    # 2026-01-15 is a Thursday: Jan 1 is a Thursday too, so three Thursdays have
    # been reached (1st, 8th, 15th) but only two Fridays (2nd, 9th)
    actual = FrequencyStats(
        [_row(date(2026, 1, 1), 5)], today=date(2026, 1, 15)
    ).weekday_profile()

    assert actual[3].calendar_days == 3
    assert actual[4].calendar_days == 2


def test_weekday_profile_counts_every_occurrence_of_a_year_already_over():
    # 2025 has 53 Wednesdays (Jan 1 was one) and 52 of every other weekday
    actual = FrequencyStats(
        [_row(date(2025, 1, 1), 5)], today=date(2026, 6, 15)
    ).weekday_profile()

    assert [point.calendar_days for point in actual] == [52, 52, 53, 52, 52, 52, 52]


def test_weekday_profile_counts_a_weekday_not_yet_reached_as_zero():
    # Jan 1 2026 is a Thursday, so on Jan 2 no Saturday has occurred at all
    actual = FrequencyStats(
        [_row(date(2026, 1, 1), 5)], today=date(2026, 1, 2)
    ).weekday_profile()

    assert actual[5].calendar_days == 0
    assert actual[5].drinking_day_share == 0.0
    assert actual[5].intensity == 0.0


def test_weekday_profile_counts_distinct_dates_not_rows():
    # two Drinks on one Monday are one Drinking day, as everywhere else
    rows = [
        _row(date(2026, 1, 5), 3),
        _row(date(2026, 1, 5), 4),
        _row(date(2026, 1, 12), 2),
    ]

    actual = FrequencyStats(rows, today=date(2026, 6, 15)).weekday_profile()

    assert actual[0].drinking_days == 2
    assert actual[0].stdav == 9.0


def test_weekday_profile_rates_are_per_weekday_not_off_the_year_total():
    # by Monday 2026-01-19 three Mondays have passed but only two Tuesdays, so
    # the weekdays differ in denominator as well as total
    rows = [
        _row(date(2026, 1, 5), 4),  # Monday
        _row(date(2026, 1, 12), 8),  # Monday
        _row(date(2026, 1, 6), 3),  # Tuesday
    ]

    actual = FrequencyStats(rows, today=date(2026, 1, 19)).weekday_profile()

    assert actual[0].calendar_days == 3
    assert actual[0].drinking_day_share == pytest.approx(2 / 3)
    assert actual[0].intensity == 6.0
    assert actual[1].calendar_days == 2
    assert actual[1].drinking_day_share == pytest.approx(1 / 2)
    assert actual[1].intensity == 3.0


def test_weekday_profile_on_no_records_is_seven_zeroed_points():
    actual = FrequencyStats(today=date(2026, 6, 15)).weekday_profile()

    assert len(actual) == 7
    assert all(point.drinking_days == 0 for point in actual)
    assert all(point.stdav == 0.0 for point in actual)
    assert all(point.drinking_day_share == 0.0 for point in actual)
    assert all(point.intensity == 0.0 for point in actual)


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
def test_weekday_profile_is_the_same_figure_under_every_drink_type(drink_type):
    # the rate is a ratio and the intensity is a harm metric, so neither follows
    # the drink-type dropdown — this pins both against a later "conversion fix"
    ratio = DrinkConverter(drink_type).ratio
    rows = [_row(date(2026, 1, 5), 6, qty=6 * ratio)]

    actual = FrequencyStats(rows, today=date(2026, 1, 19)).weekday_profile()

    assert actual[0].intensity == 6.0
    assert actual[0].stdav == 6.0
    assert actual[0].drinking_day_share == pytest.approx(1 / 3)


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
