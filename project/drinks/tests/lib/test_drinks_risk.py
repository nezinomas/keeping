from datetime import date

import time_machine

from ...lib.drinks_risk import (
    HEAVY_DAY_STDAV,
    WEEKLY_HIGH_RISK_STDAV,
    WEEKLY_LOW_RISK_STDAV,
    RiskStats,
)
from ...lib.drinks_stats import DataRow


def _row(dt: date, stdav: float) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=0.0)


# -------------------------------------------------------------------------------------
#                                                                             constants
# -------------------------------------------------------------------------------------
def test_thresholds_are_ordered():
    assert 0 < WEEKLY_LOW_RISK_STDAV < WEEKLY_HIGH_RISK_STDAV
    assert HEAVY_DAY_STDAV > 0


# -------------------------------------------------------------------------------------
#                                                                       current_year
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-06-15")
def test_current_year_defaults_to_today_when_no_records():
    assert RiskStats(current_daily=[]).current_year == 2026


@time_machine.travel("2026-06-15")
def test_current_year_defaults_to_today_with_no_arguments():
    assert RiskStats().current_year == 2026


@time_machine.travel("2026-06-15")
def test_current_year_taken_from_records():
    stats = RiskStats(current_daily=[_row(date(2025, 3, 1), 5)])
    assert stats.current_year == 2025


@time_machine.travel("2026-06-15")
def test_past_clipped_records_is_cached():
    current = [_row(date(2026, 1, 1), 7)]
    past = [_row(date(2025, 1, 1), 7)]
    stats = RiskStats(current_daily=current, past_daily=past)
    assert stats._past_clipped_records is stats._past_clipped_records


# -------------------------------------------------------------------------------------
#                                                                       weekly_series
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-01-15")
def test_weekly_series_dense_from_first_week_to_current():
    # 2026-01-01 is Thursday -> week starts Mon 2025-12-29
    # 2026-01-15 is Thursday -> week starts Mon 2026-01-12
    series = RiskStats(current_daily=[]).weekly_series()

    assert [w.stdav for w in series] == [0.0, 0.0, 0.0]
    assert series[0].label == "2025-12-29"
    assert series[0].end == "2026-01-04"  # Sunday of the first week
    assert series[-1].label == "2026-01-12"
    assert series[-1].end == "2026-01-18"


@time_machine.travel("2026-01-15")
def test_weekly_series_sums_records_into_their_week():
    rows = [_row(date(2026, 1, 5), 4), _row(date(2026, 1, 7), 3)]
    series = RiskStats(current_daily=rows).weekly_series()

    totals = {w.label: w.stdav for w in series}
    assert totals["2026-01-05"] == 7.0
    assert totals["2025-12-29"] == 0.0


@time_machine.travel("2026-06-15")
def test_weekly_series_for_past_year_spans_to_dec_31():
    # viewing 2025 while today is 2026 -> year end is 2025-12-31 (Wed) -> Mon 2025-12-29
    series = RiskStats(current_daily=[_row(date(2025, 3, 1), 5)]).weekly_series()

    assert series[0].label == "2024-12-30"
    assert series[-1].label == "2025-12-29"


def test_week_mondays_generator():
    start = date(2026, 1, 5)
    end = date(2026, 1, 19)
    mondays = list(RiskStats._week_mondays(start, end))

    assert mondays == [date(2026, 1, 5), date(2026, 1, 12), date(2026, 1, 19)]


# -------------------------------------------------------------------------------------
#                                                                       current_week
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-01-15")
def test_current_week_low():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 13), 5)])
    week = stats.current_week()

    assert week.stdav == 5.0
    assert week.state == "low"
    assert week.label == "2026-01-12"
    assert week.end == "2026-01-18"
    assert week.has_data is True


@time_machine.travel("2026-01-15")
def test_current_week_medium_between_thresholds():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 13), 15)])

    assert stats.current_week().state == "medium"


@time_machine.travel("2026-01-15")
def test_current_week_high_above_high_threshold():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 13), 30)])

    assert stats.current_week().state == "high"


@time_machine.travel("2026-01-15")
def test_current_week_zero_when_no_drinks_is_low():
    week = RiskStats(current_daily=[]).current_week()

    assert week.stdav == 0.0
    assert week.state == "low"


# -------------------------------------------------------------------------------------
#                                                                zone classification
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-01-15")
def test_zone_exactly_at_low_threshold_is_low():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 13), WEEKLY_LOW_RISK_STDAV)])

    assert stats.current_week().state == "low"


@time_machine.travel("2026-01-15")
def test_zone_exactly_at_high_threshold_is_medium():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 13), WEEKLY_HIGH_RISK_STDAV)])

    assert stats.current_week().state == "medium"


@time_machine.travel("2026-01-15")
def test_zone_classifies_on_rounded_value_not_raw():
    # 11.24 rounds (display) to 11.2 == the low threshold -> must stay "low",
    # even though the raw value is technically over it
    stats = RiskStats(current_daily=[_row(date(2026, 1, 13), 11.24)])

    week = stats.current_week()
    assert week.stdav == 11.2
    assert week.state == "low"


# -------------------------------------------------------------------------------------
#                                                                        worst_week
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_worst_week_empty_without_data():
    week = RiskStats(current_daily=[]).worst_week()

    assert week.has_data is False
    assert week.state == "empty"
    assert week.stdav == 0.0


@time_machine.travel("2026-03-01")
def test_worst_week_picks_highest_week():
    # 2026-02-09 is a Monday
    rows = [_row(date(2026, 1, 5), 4), _row(date(2026, 2, 9), 30)]
    week = RiskStats(current_daily=rows).worst_week()

    assert week.stdav == 30.0
    assert week.state == "high"
    assert week.label == "2026-02-09"
    assert week.end == "2026-02-15"  # Sunday of that week


# -------------------------------------------------------------------------------------
#                                                                        heavy_days
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-06-01")
def test_heavy_days_counts_days_over_threshold():
    rows = [_row(date(2026, 1, 1), 7), _row(date(2026, 1, 2), 3)]
    heavy = RiskStats(current_daily=rows).heavy_days()

    assert heavy.current == 1
    assert heavy.has_past is False


@time_machine.travel("2026-06-01")
def test_heavy_days_improving_vs_last_year():
    current = [_row(date(2026, 1, 1), 7)]
    past = [_row(date(2025, 1, 1), 7), _row(date(2025, 2, 1), 8)]
    heavy = RiskStats(current_daily=current, past_daily=past).heavy_days()

    assert heavy.current == 1
    assert heavy.previous == 2
    assert heavy.improving is True
    assert heavy.has_past is True


@time_machine.travel("2026-06-01")
def test_heavy_days_worsening_vs_last_year():
    current = [_row(date(2026, 1, 1), 7), _row(date(2026, 2, 1), 8)]
    past = [_row(date(2025, 1, 1), 7)]
    heavy = RiskStats(current_daily=current, past_daily=past).heavy_days()

    assert heavy.improving is False


@time_machine.travel("2026-02-01")
def test_heavy_days_past_clipped_by_day_of_year():
    # today is day-of-year 32; last year's Dec 31 must not count
    current = [_row(date(2026, 1, 1), 7)]
    past = [_row(date(2025, 1, 1), 8), _row(date(2025, 12, 31), 9)]
    heavy = RiskStats(current_daily=current, past_daily=past).heavy_days()

    assert heavy.previous == 1


@time_machine.travel("2026-06-01")
def test_heavy_days_past_dec31_not_dropped_when_past_year_is_leap():
    # viewing completed year 2025 (365 days); the immediately preceding year,
    # 2024, was a leap year (366 days) -> ordinal day-of-year numbers for Dec 31
    # don't line up across the boundary (2025-12-31 is day 365, 2024-12-31 is
    # day 366), so a naive day-of-year cutoff would wrongly drop 2024-12-31
    current = [_row(date(2025, 1, 1), 7)]
    past = [_row(date(2024, 12, 31), 9)]
    heavy = RiskStats(current_daily=current, past_daily=past).heavy_days()

    assert heavy.previous == 1


# -------------------------------------------------------------------------------------
#                                                                 weeks_over_guideline
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-06-01")
def test_weeks_over_guideline_counts_current_year():
    rows = [_row(date(2026, 1, 5), 15)]  # one week over 11.2
    over = RiskStats(current_daily=rows).weeks_over_guideline()

    assert over.current == 1
    assert over.has_past is False


@time_machine.travel("2026-06-01")
def test_weeks_over_guideline_vs_last_year():
    current = [_row(date(2026, 1, 5), 15)]
    past = [_row(date(2025, 1, 6), 15), _row(date(2025, 2, 3), 20)]
    over = RiskStats(current_daily=current, past_daily=past).weeks_over_guideline()

    assert over.current == 1
    assert over.previous == 2
    assert over.improving is True


# -------------------------------------------------------------------------------------
#                                                                 monthly_heavy_days
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-12-31")
def test_monthly_heavy_days():
    rows = [
        _row(date(2026, 1, 1), 7),
        _row(date(2026, 1, 2), 8),
        _row(date(2026, 3, 1), 9),
        _row(date(2026, 3, 2), 2),
    ]
    counts = RiskStats(current_daily=rows).monthly_heavy_days()

    assert len(counts) == 12
    assert counts[0] == 2
    assert counts[2] == 1
    assert counts[5] == 0
