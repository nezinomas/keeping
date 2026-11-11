from dataclasses import dataclass
from datetime import date, timedelta

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

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


@pytest.mark.parametrize(
    "year, today, expect",
    [
        pytest.param(2026, date(2026, 12, 31), True, id="the_running_year"),
        pytest.param(2025, date(2026, 1, 1), False, id="a_finished_year"),
        pytest.param(2027, date(2026, 6, 15), False, id="a_coming_year"),
    ],
)
def test_is_current_only_while_the_year_is_the_one_running(year, today, expect):
    assert YearBoundary(year=year, today=today).is_current is expect


@pytest.mark.parametrize(
    "year, today, expect",
    [
        pytest.param(2026, date(2026, 3, 1), 60, id="up_to_today_in_the_current_year"),
        pytest.param(2025, date(2026, 6, 15), 365, id="the_whole_of_a_finished_year"),
        pytest.param(2024, date(2026, 6, 15), 366, id="the_leap_day"),
        pytest.param(2027, date(2026, 6, 15), 0, id="none_of_a_coming_year"),
    ],
)
def test_days_elapsed_counts_to_today_or_to_the_end_of_the_year(year, today, expect):
    assert YearBoundary(year=year, today=today).days_elapsed == expect


def _weeks_reached(year: int, today: date) -> int:
    """The ISO weeks of `year` its days up to today touch; a start inside last ISO
    year's week counts as week one."""
    last = min(today, date(year, 12, 31))
    days = [
        date(year, 1, 1) + timedelta(n)
        for n in range((last - date(year, 1, 1)).days + 1)
    ]
    if not days:
        return 0

    weeks = {day.isocalendar().week for day in days if day.isocalendar().year == year}
    return len(weeks) or 1


@st.composite
def years_and_days(draw):
    today = draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2040, 12, 31)))
    year = today.year + draw(st.sampled_from([-2, -1, 0, 0, 0, 1]))

    return year, today, _weeks_reached(year, today)


@given(years_and_days())
@example((2026, date(2026, 7, 31), 31))
# 52, not the 53 an "is it leap / does it start on a Wednesday" rule gives
@example((2025, date(2026, 7, 31), 52))
@example((2020, date(2026, 7, 31), 53))
# 2027-01-01 is week 53 of ISO year 2026: the raw number would divide by 53
@example((2027, date(2027, 1, 1), 1))
# 2024-12-30 is week 1 of ISO year 2025, and 2024 has 52 weeks
@example((2024, date(2024, 12, 30), 52))
@example((2027, date(2026, 6, 15), 0))
def test_weeks_elapsed_counts_iso_weeks_inside_the_year(case):
    year, today, weeks = case

    assert YearBoundary(year=year, today=today).weeks_elapsed == weeks


@pytest.mark.parametrize(
    "year, today, weekday, expect",
    [
        # 2025 began on a Wednesday, so it holds 53 of them
        pytest.param(
            2025, date(2026, 6, 15), 2, 53, id="every_occurrence_of_a_finished_year"
        ),
        # 2026 began on a Thursday: by Thursday Jan 15, Fridays 2nd and 9th
        pytest.param(
            2026, date(2026, 1, 15), 4, 2, id="those_reached_in_the_running_year"
        ),
        pytest.param(
            2026, date(2026, 1, 2), 5, 0, id="none_before_its_first_day_this_year"
        ),
        # 2027 begins on a Friday
        pytest.param(2027, date(2026, 6, 15), 4, 0, id="none_of_a_coming_year"),
    ],
)
def test_weekdays_reached_counts_one_weekday_inside_the_year(
    year, today, weekday, expect
):
    assert YearBoundary(year=year, today=today).weekdays_reached(weekday) == expect


@pytest.mark.parametrize(
    "year, expect",
    [
        pytest.param(2026, 8, id="the_month_reached_in_the_current_year"),
        pytest.param(2025, 12, id="all_twelve_of_a_finished_year"),
        pytest.param(2027, 0, id="none_of_a_coming_year"),
    ],
)
def test_months_elapsed_counts_the_months_the_year_has_reached(year, expect):
    assert YearBoundary(year=year, today=date(2026, 8, 11)).months_elapsed == expect


@pytest.mark.parametrize(
    "year, today, dates, expect",
    [
        pytest.param(
            2026,
            date(2026, 2, 1),
            [date(2025, 1, 1), date(2025, 2, 1), date(2025, 12, 31)],
            [date(2025, 1, 1), date(2025, 2, 1)],
            id="to_today_while_the_year_runs",
        ),
        pytest.param(
            2027,
            date(2026, 6, 15),
            [date(2026, 6, 15), date(2026, 6, 16)],
            [date(2026, 6, 15)],
            id="the_year_before_a_coming_year_only_to_today",
        ),
        # 2024-12-31 is day 366 and 2025-12-31 is day 365, so an ordinal day-of-year
        # cutoff would drop it; matching on (month, day) keeps it
        pytest.param(
            2025,
            date(2026, 6, 15),
            [date(2024, 12, 31)],
            [date(2024, 12, 31)],
            id="dec_31_of_a_leap_year_before_a_finished_year",
        ),
        pytest.param(
            2025,
            date(2026, 6, 15),
            [date(2024, 1, 1), date(2024, 7, 15), date(2024, 12, 31)],
            [date(2024, 1, 1), date(2024, 7, 15), date(2024, 12, 31)],
            id="the_whole_year_before_a_finished_year",
        ),
        pytest.param(2026, date(2026, 2, 1), [], [], id="nothing"),
    ],
)
def test_clip_keeps_rows_up_to_the_same_month_and_day(year, today, dates, expect):
    boundary = YearBoundary(year=year, today=today)

    kept = boundary.clip([_row(day) for day in dates])

    assert [row.date for row in kept] == expect


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
        pytest.param(
            2027,
            date(2026, 6, 15),
            date(2026, 6, 15),
            id="today_before_a_coming_year",
        ),
    ],
)
def test_previous_end_date_is_a_year_back(year, today, expect):
    assert YearBoundary(year=year, today=today).previous_end_date == expect


@pytest.mark.parametrize(
    "year, day, expect",
    [
        pytest.param(2025, date(2024, 3, 1), date(2025, 3, 1), id="same_month_and_day"),
        pytest.param(
            2025, date(2024, 2, 29), date(2025, 2, 28), id="leap_day_folds_into_feb_28"
        ),
        pytest.param(
            2024, date(2023, 2, 28), date(2024, 2, 28), id="feb_28_onto_a_leap_year"
        ),
    ],
)
def test_this_years_day_matches_month_and_day(year, day, expect):
    boundary = YearBoundary(year=year, today=date(2026, 8, 11))

    assert boundary.this_years_day(day) == expect


@pytest.mark.parametrize(
    "year, span, previous_span",
    [
        pytest.param(
            2026,
            (date(2026, 1, 1), date(2026, 8, 11)),
            (date(2025, 1, 1), date(2025, 8, 11)),
            id="new_year_to_today_and_a_year_back",
        ),
        pytest.param(
            2025,
            (date(2025, 1, 1), date(2025, 12, 31)),
            (date(2024, 1, 1), date(2024, 12, 31)),
            id="whole_finished_years",
        ),
    ],
)
def test_spans_run_from_new_year_to_the_end_dates(year, span, previous_span):
    boundary = YearBoundary(year=year, today=date(2026, 8, 11))

    assert (boundary.span, boundary.previous_span) == (span, previous_span)
