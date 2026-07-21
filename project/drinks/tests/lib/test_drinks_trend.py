from datetime import date

import pytest
import time_machine

from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DataRow
from ...lib.drinks_trend import TrendStats


@pytest.fixture(name="converter")
def fixture_converter():
    return DrinkConverter("beer")


def _row(dt: date, stdav: float) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=0.0)


# -------------------------------------------------------------------------------------
#                                                                    categories / dense
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_categories_span_from_jan_first_to_today(converter):
    stats = TrendStats(converter, current_daily=[])

    # 2026 is not a leap year: 31 (Jan) + 28 (Feb) + 1 = 60
    assert len(stats.categories) == 60
    assert stats.categories[0] == "2026-01-01"
    assert stats.categories[-1] == "2026-03-01"


@time_machine.travel("2026-06-15")
def test_past_year_spans_full_year(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2025, 5, 5), 1)])

    assert len(stats.categories) == 365
    assert stats.categories[0] == "2025-01-01"
    assert stats.categories[-1] == "2025-12-31"


# -------------------------------------------------------------------------------------
#                                                                       rolling average
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-01-05")
def test_rolling_average_divides_by_full_window(converter):
    # beer: 1 stdav -> 200 ml, so 5 stdav -> 1000 ml on the first day only
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 5)])

    # every point divides by the FULL window (no start-of-year spike from a
    # short denominator); the 1000 ml day stays inside both windows for Jan 1-5
    assert stats.rolling(7) == pytest.approx([1000 / 7] * 5)
    assert stats.rolling(30) == pytest.approx([1000 / 30] * 5)


@time_machine.travel("2026-01-02")
def test_rolling_average_seeds_from_previous_december(converter):
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 1), 5)],  # 1000 ml
        past_daily=[_row(date(2025, 12, 31), 5)],  # 1000 ml, inside the window
    )

    # Jan 1's 7-day mean pulls in Dec 31 -> (1000 + 1000) / 7
    assert stats.rolling(7)[0] == pytest.approx(2000 / 7)


# -------------------------------------------------------------------------------------
#                                                             period vs previous period
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-02-01")
def test_period_improving_when_recent_is_lower(converter):
    # last 14 days (Jan 18 - Feb 1): 3; prior 14 days (Jan 4 - Jan 18): 9
    rows = [_row(date(2026, 1, 25), 3), _row(date(2026, 1, 10), 9)]
    stats = TrendStats(converter, current_daily=rows)

    p = stats.period(14)

    assert p.current == 3
    assert p.past == 9
    assert p.pct == 66.7  # abs(3 - 9) / 9 * 100
    assert p.improving is True
    assert p.has_data is True


@time_machine.travel("2026-02-01")
def test_period_worsening_when_recent_is_higher(converter):
    rows = [_row(date(2026, 1, 25), 10), _row(date(2026, 1, 10), 2)]
    stats = TrendStats(converter, current_daily=rows)

    p = stats.period(14)

    assert p.current == 10
    assert p.past == 2
    assert p.improving is False


@time_machine.travel("2026-01-20")
def test_period_without_prior_baseline(converter):
    # only recent drinking, nothing in the previous window -> no percentage
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 15), 4)])

    p = stats.period(14)

    assert p.current == 4
    assert p.past == 0.0
    assert p.pct is None
    assert p.has_data is True


@time_machine.travel("2026-06-01")
def test_period_no_data(converter):
    stats = TrendStats(converter, current_daily=[])

    assert stats.period(14).has_data is False


@time_machine.travel("2026-01-20")
def test_period_straddles_year_boundary(converter):
    # prior window reaches into last December -> must use previous-year data
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 10), 2)],
        past_daily=[_row(date(2025, 12, 30), 8)],
    )

    p = stats.period(14)

    assert p.current == 2
    assert p.past == 8
    assert p.improving is True


# -------------------------------------------------------------------------------------
#                                                            YTD vs same period last yr
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_ytd_vs_last_year(converter):
    current = [_row(date(2026, 1, 1), 10), _row(date(2026, 2, 1), 5)]
    past = [
        _row(date(2025, 1, 1), 20),
        _row(date(2025, 4, 10), 100),  # day-of-year > today's, must be excluded
    ]
    stats = TrendStats(converter, current_daily=current, past_daily=past)

    ytd = stats.ytd()

    assert ytd.current == 15
    assert ytd.past == 20
    assert ytd.pct == 25.0  # magnitude; direction is carried by `improving`
    assert ytd.improving is True
    assert ytd.has_past is True


@time_machine.travel("2026-03-01")
def test_ytd_without_past_data(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 10)])

    ytd = stats.ytd()

    assert ytd.current == 10
    assert ytd.has_past is False
    assert ytd.pct is None


# -------------------------------------------------------------------------------------
#                                                             projection to year-end
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-01-10")
def test_projection_over_target(converter):
    # 10 stdav -> 2000 ml over 10 days = 200 ml/day pace
    stats = TrendStats(
        converter, current_daily=[_row(date(2026, 1, 1), 10)], target=100
    )

    projection = stats.projection()

    assert projection.projected_l == 73.0  # 200 ml/day * 365 / 1000
    assert projection.target_l == 36.5  # 100 ml/day * 365 / 1000
    assert projection.pct == 100.0
    assert projection.over is True
    assert projection.has_target is True


@time_machine.travel("2026-01-10")
def test_projection_without_target(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 10)])

    projection = stats.projection()

    assert projection.has_target is False
    assert projection.pct is None
