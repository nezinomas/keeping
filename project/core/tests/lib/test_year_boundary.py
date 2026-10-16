from dataclasses import dataclass
from datetime import date

import pytest

from ...lib.year_boundary import YearBoundary


@dataclass(frozen=True)
class Row:
    """A row of an app's own shape — all the boundary asks for is a date."""

    date: date


def _row(dt: date) -> Row:
    return Row(date=dt)


@pytest.mark.parametrize(
    "year, expect",
    [
        pytest.param(2026, date(2026, 6, 15), id="today_while_the_year_runs"),
        pytest.param(2025, date(2025, 12, 31), id="dec_31_for_a_finished_year"),
        # next year is selectable in the app; it ends when that year does, not today
        pytest.param(2027, date(2027, 12, 31), id="dec_31_for_a_year_not_started_yet"),
    ],
)
def test_end_date_is_today_only_while_the_year_runs(year, expect):
    boundary = YearBoundary(year=year, today=date(2026, 6, 15))

    assert boundary.end_date == expect


def test_is_current_only_while_the_year_is_the_one_running():
    assert YearBoundary(year=2026, today=date(2026, 12, 31)).is_current is True
    assert YearBoundary(year=2025, today=date(2026, 1, 1)).is_current is False
    assert YearBoundary(year=2027, today=date(2026, 6, 15)).is_current is False


@pytest.mark.parametrize(
    "year, today, expect",
    [
        pytest.param(2026, date(2026, 3, 1), 60, id="up_to_today_in_the_current_year"),
        pytest.param(2025, date(2026, 6, 15), 365, id="the_whole_of_a_finished_year"),
        pytest.param(2024, date(2026, 6, 15), 366, id="the_leap_day"),
    ],
)
def test_days_elapsed_counts_to_today_or_to_the_end_of_the_year(year, today, expect):
    assert YearBoundary(year=year, today=today).days_elapsed == expect


@pytest.mark.parametrize(
    "year, today, expect",
    [
        pytest.param(2026, date(2026, 7, 31), 31, id="this_week_in_the_current_year"),
        # 52, not the 53 an "is it leap / does it start on a Wednesday" rule gives
        pytest.param(
            2025, date(2026, 7, 31), 52, id="iso_week_count_of_a_finished_year"
        ),
        pytest.param(2020, date(2026, 7, 31), 53, id="53_in_a_year_with_53_weeks"),
        # 2027-01-01 is week 53 of ISO year 2026: the raw number would divide by 53
        pytest.param(
            2027, date(2027, 1, 1), 1, id="one_in_a_january_iso_counts_as_last_year"
        ),
        # 2024-12-30 is week 1 of ISO year 2025, and 2024 has 52 weeks
        pytest.param(
            2024,
            date(2024, 12, 30),
            52,
            id="full_count_in_a_december_iso_counts_as_next_year",
        ),
    ],
)
def test_weeks_elapsed_counts_iso_weeks_inside_the_year(year, today, expect):
    assert YearBoundary(year=year, today=today).weeks_elapsed == expect


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


@pytest.mark.parametrize(
    "year, today, expect",
    [
        pytest.param(
            2026,
            date(2026, 8, 11),
            date(2025, 8, 11),
            id="same_month_and_day_a_year_back",
        ),
        pytest.param(
            2020,
            date(2026, 8, 11),
            date(2019, 12, 31),
            id="whole_year_before_a_finished_one",
        ),
        pytest.param(
            2024,
            date(2024, 2, 29),
            date(2023, 2, 28),
            id="leap_day_clamped_onto_a_common_year",
        ),
    ],
)
def test_previous_end_date_is_a_year_back(year, today, expect):
    assert YearBoundary(year=year, today=today).previous_end_date == expect


@pytest.mark.parametrize(
    "year, expect",
    [
        pytest.param(
            2026, (date(2026, 1, 1), date(2026, 8, 11)), id="new_year_to_today"
        ),
        pytest.param(2025, (date(2025, 1, 1), date(2025, 12, 31)), id="finished_year"),
    ],
)
def test_span_ends_today_only_while_the_year_runs(year, expect):
    assert YearBoundary(year=year, today=date(2026, 8, 11)).span == expect


def test_previous_span_stops_on_the_same_day_a_year_back():
    boundary = YearBoundary(year=2026, today=date(2026, 8, 11))

    assert boundary.previous_span == (date(2025, 1, 1), date(2025, 8, 11))
