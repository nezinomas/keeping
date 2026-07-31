from datetime import date

import time_machine

from ...lib.drinks_stats import DataRow
from ...lib.drinks_year import YearBoundary


def _row(dt: date) -> DataRow:
    return DataRow(date=dt, qty=0.0, stdav=0.0)


# -------------------------------------------------------------------------------------
#                                                                                  year
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-06-15")
def test_year_comes_from_the_first_record():
    assert YearBoundary.from_records([_row(date(2025, 3, 1))]).year == 2025


@time_machine.travel("2026-06-15")
def test_year_falls_back_to_today_without_records():
    assert YearBoundary.from_records().year == 2026


@time_machine.travel("2026-06-15")
def test_today_can_be_given_instead_of_the_clock():
    boundary = YearBoundary.from_records(today=date(2019, 5, 4))

    assert boundary.year == 2019
    assert boundary.today == date(2019, 5, 4)


# -------------------------------------------------------------------------------------
#                                                                              end_date
# -------------------------------------------------------------------------------------
def test_end_date_is_today_while_the_year_runs():
    boundary = YearBoundary(year=2026, today=date(2026, 6, 15))

    assert boundary.end_date == date(2026, 6, 15)


def test_end_date_is_dec_31_for_a_finished_year():
    boundary = YearBoundary(year=2025, today=date(2026, 6, 15))

    assert boundary.end_date == date(2025, 12, 31)


def test_end_date_is_dec_31_for_a_year_not_started_yet():
    # next year is selectable in the app; it ends when that year does, not today
    boundary = YearBoundary(year=2027, today=date(2026, 6, 15))

    assert boundary.end_date == date(2027, 12, 31)


# -------------------------------------------------------------------------------------
#                                                                          days_elapsed
# -------------------------------------------------------------------------------------
def test_days_elapsed_counts_up_to_today_in_the_current_year():
    boundary = YearBoundary(year=2026, today=date(2026, 3, 1))

    assert boundary.days_elapsed == 60  # 31 (Jan) + 28 (Feb) + 1


def test_days_elapsed_is_the_whole_of_a_finished_year():
    boundary = YearBoundary(year=2025, today=date(2026, 6, 15))

    assert boundary.days_elapsed == 365


def test_days_elapsed_counts_the_leap_day():
    boundary = YearBoundary(year=2024, today=date(2026, 6, 15))

    assert boundary.days_elapsed == 366


# -------------------------------------------------------------------------------------
#                                                                                  clip
# -------------------------------------------------------------------------------------
def test_clip_keeps_rows_up_to_the_same_month_and_day():
    boundary = YearBoundary(year=2026, today=date(2026, 2, 1))
    rows = [_row(date(2025, 1, 1)), _row(date(2025, 2, 1)), _row(date(2025, 12, 31))]

    kept = boundary.clip(rows)

    assert [row.date for row in kept] == [date(2025, 1, 1), date(2025, 2, 1)]


def test_clip_keeps_dec_31_of_a_leap_year_before_a_finished_year():
    # 2024-12-31 is day 366 and 2025-12-31 is day 365, so an ordinal day-of-year
    # cutoff would drop it; matching on (month, day) keeps it
    boundary = YearBoundary(year=2025, today=date(2026, 6, 15))

    kept = boundary.clip([_row(date(2024, 12, 31))])

    assert [row.date for row in kept] == [date(2024, 12, 31)]


def test_clip_keeps_the_whole_year_before_a_finished_year():
    boundary = YearBoundary(year=2025, today=date(2026, 6, 15))
    rows = [_row(date(2024, 1, 1)), _row(date(2024, 7, 15)), _row(date(2024, 12, 31))]

    assert len(boundary.clip(rows)) == 3


def test_clip_of_nothing_is_empty():
    boundary = YearBoundary(year=2026, today=date(2026, 2, 1))

    assert boundary.clip([]) == []
