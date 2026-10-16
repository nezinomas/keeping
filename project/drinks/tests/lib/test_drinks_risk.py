from datetime import date

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.drinks_risk import (
    CALENDAR_LEVELS,
    HEAVY_DAY_STDAV,
    MONTHLY_HEAVY_HIGH_RISK,
    MONTHLY_HEAVY_LOW_RISK,
    WEEKLY_HIGH_RISK_STDAV,
    WEEKLY_LOW_RISK_STDAV,
    RiskStats,
)
from ...lib.drinks_stats import DataRow


def _row(dt: date, stdav: float) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=0.0)


def test_thresholds_are_ordered():
    assert 0 < WEEKLY_LOW_RISK_STDAV < WEEKLY_HIGH_RISK_STDAV
    assert 0 < MONTHLY_HEAVY_LOW_RISK < MONTHLY_HEAVY_HIGH_RISK
    assert HEAVY_DAY_STDAV > 0


def test_the_calendars_top_level_starts_at_the_heavy_day_threshold():
    assert CALENDAR_LEVELS[-1] == HEAVY_DAY_STDAV


@pytest.mark.parametrize(
    "rows",
    [
        pytest.param([], id="an_empty_year"),
        pytest.param([_row(date(1998, 3, 1), 5)], id="a_year_with_drinks"),
    ],
)
def test_current_year_is_the_year_the_caller_views(rows):
    stats = RiskStats(current_daily=rows, year=1998, today=date(1999, 6, 1))

    # Dec 31 1998 is a Thursday, so the year's last week starts on Monday the 28th
    assert (stats.current_year, stats.weekly_series()[-1].label) == (1998, "1998-12-28")


def test_weekly_series_dense_from_first_week_to_current():
    # 2026-01-01 is Thursday -> week starts Mon 2025-12-29
    # 2026-01-15 is Thursday -> week starts Mon 2026-01-12
    series = RiskStats(
        current_daily=[], year=2026, today=date(2026, 1, 15)
    ).weekly_series()

    assert [w.stdav for w in series] == [0.0, 0.0, 0.0]
    assert series[0].label == "2025-12-29"
    assert series[0].end == "2026-01-04"  # Sunday of the first week
    assert series[-1].label == "2026-01-12"
    assert series[-1].end == "2026-01-18"


def test_weekly_series_sums_records_into_their_week():
    rows = [_row(date(2026, 1, 5), 4), _row(date(2026, 1, 7), 3)]
    series = RiskStats(
        current_daily=rows, year=2026, today=date(2026, 1, 15)
    ).weekly_series()

    totals = {w.label: w.stdav for w in series}
    assert totals["2026-01-05"] == 7.0
    assert totals["2025-12-29"] == 0.0


def test_weekly_series_for_past_year_spans_to_dec_31():
    # viewing 2025 while today is 2026 -> year end is 2025-12-31 (Wed) -> Mon 2025-12-29
    series = RiskStats(
        current_daily=[_row(date(2025, 3, 1), 5)], year=2025, today=date(2026, 6, 15)
    ).weekly_series()

    assert series[0].label == "2024-12-30"
    assert series[-1].label == "2025-12-29"


@given(stdavs=st.lists(st.integers(0, 4000).map(lambda c: c / 100), max_size=1))
@example(stdavs=[])
@example(stdavs=[5])
@example(stdavs=[15])
@example(stdavs=[30])
@example(stdavs=[WEEKLY_LOW_RISK_STDAV])
@example(stdavs=[WEEKLY_HIGH_RISK_STDAV])
# 11.24 shows as 11.2, the low threshold: classified on the shown value, so still low
@example(stdavs=[11.24])
def test_current_week_state_follows_the_thresholds(stdavs):
    shown = round(sum(stdavs), 1)
    state = "low"
    if shown > WEEKLY_LOW_RISK_STDAV:
        state = "medium"
    if shown > WEEKLY_HIGH_RISK_STDAV:
        state = "high"

    rows = [_row(date(2026, 1, 13), stdav) for stdav in stdavs]
    week = RiskStats(
        current_daily=rows, year=2026, today=date(2026, 1, 15)
    ).current_week()

    assert week.stdav == shown
    assert week.state == state
    assert week.label == "2026-01-12"
    assert week.end == "2026-01-18"
    assert week.has_data is True


def test_worst_week_empty_without_data():
    week = RiskStats(current_daily=[], year=2026, today=date(2026, 3, 1)).worst_week()

    assert week.has_data is False
    assert week.state == "empty"
    assert week.stdav == 0.0


def test_worst_week_picks_highest_week():
    # 2026-02-09 is a Monday
    rows = [_row(date(2026, 1, 5), 4), _row(date(2026, 2, 9), 30)]
    week = RiskStats(current_daily=rows, year=2026, today=date(2026, 3, 1)).worst_week()

    assert week.stdav == 30.0
    assert week.state == "high"
    assert week.label == "2026-02-09"
    assert week.end == "2026-02-15"  # Sunday of that week


def test_heavy_days_counts_days_over_threshold():
    rows = [_row(date(2026, 1, 1), 7), _row(date(2026, 1, 2), 3)]
    heavy = RiskStats(
        current_daily=rows, year=2026, today=date(2026, 6, 1)
    ).heavy_days()

    assert heavy.current == 1
    assert heavy.has_past is False


@pytest.mark.parametrize(
    "current, past, previous, improving",
    [
        pytest.param(
            [_row(date(2026, 1, 1), 7)],
            [_row(date(2025, 1, 1), 7), _row(date(2025, 2, 1), 8)],
            2,
            True,
            id="improving",
        ),
        pytest.param(
            [_row(date(2026, 1, 1), 7), _row(date(2026, 2, 1), 8)],
            [_row(date(2025, 1, 1), 7)],
            1,
            False,
            id="worsening",
        ),
    ],
)
def test_heavy_days_against_last_year(current, past, previous, improving):
    heavy = RiskStats(
        current_daily=current, past_daily=past, year=2026, today=date(2026, 6, 1)
    ).heavy_days()

    assert heavy.current == len(current)
    assert heavy.previous == previous
    assert heavy.improving is improving
    assert heavy.has_past is True


@pytest.mark.parametrize(
    "today, current, past",
    [
        # today is day-of-year 32; last year's Dec 31 must not count
        pytest.param(
            "2026-02-01",
            [_row(date(2026, 1, 1), 7)],
            [_row(date(2025, 1, 1), 8), _row(date(2025, 12, 31), 9)],
            id="clipped_by_day_of_year",
        ),
        # 2024 was a leap year, so Dec 31 is day 366 there and 365 in 2025 - a
        # naive day-of-year cutoff drops 2024-12-31
        pytest.param(
            "2026-06-01",
            [_row(date(2025, 1, 1), 7)],
            [_row(date(2024, 12, 31), 9)],
            id="dec31_not_dropped_when_past_year_is_leap",
        ),
    ],
)
def test_heavy_days_past_is_clipped_to_the_same_day_of_the_year(today, current, past):
    heavy = RiskStats(
        current_daily=current,
        past_daily=past,
        year=current[0].date.year,
        today=date.fromisoformat(today),
    ).heavy_days()

    assert heavy.previous == 1


@pytest.mark.parametrize(
    "stdav, expected",
    [
        pytest.param(15, 1, id="well_over"),
        pytest.param(11.3, 1, id="just_over_the_guideline"),
        pytest.param(WEEKLY_LOW_RISK_STDAV, 0, id="exactly_the_guideline"),
        pytest.param(11.24, 0, id="rounds_down_to_the_guideline"),
    ],
)
def test_weeks_over_guideline_counts_current_year(stdav, expected):
    rows = [_row(date(2026, 1, 5), stdav)]
    over = RiskStats(
        current_daily=rows, year=2026, today=date(2026, 6, 1)
    ).weeks_over_guideline()

    assert over.current == expected
    assert over.has_past is False


def test_weeks_over_guideline_vs_last_year():
    current = [_row(date(2026, 1, 5), 15)]
    past = [_row(date(2025, 1, 6), 15), _row(date(2025, 2, 3), 20)]
    over = RiskStats(
        current_daily=current, past_daily=past, year=2026, today=date(2026, 6, 1)
    ).weeks_over_guideline()

    assert over.current == 1
    assert over.previous == 2
    assert over.improving is True


def test_monthly_heavy_days():
    rows = [
        _row(date(2026, 1, 1), 7),
        _row(date(2026, 1, 2), 8),
        _row(date(2026, 3, 1), 9),
        _row(date(2026, 3, 2), 2),
    ]
    counts = RiskStats(
        current_daily=rows, year=2026, today=date(2026, 12, 31)
    ).monthly_heavy_days()

    assert len(counts) == 12
    assert counts[0] == 2
    assert counts[2] == 1
    assert counts[5] == 0
