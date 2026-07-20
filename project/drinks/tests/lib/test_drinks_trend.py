from datetime import date

import pytest
import time_machine

from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_trend import TrendStats


@pytest.fixture(name="converter")
def fixture_converter():
    return DrinkConverter("beer")


def _row(dt: date, stdav: float) -> dict:
    return {"date": dt, "stdav": stdav, "qty": 0.0}


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
def test_rolling_average_in_ml(converter):
    # beer: 1 stdav -> 200 ml, so 5 stdav -> 1000 ml on the first day only
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 5)])

    assert stats.rolling(7) == pytest.approx([1000, 500, 1000 / 3, 250, 200])
    # window wider than the data -> same partial means
    assert stats.rolling(30) == pytest.approx([1000, 500, 1000 / 3, 250, 200])


# -------------------------------------------------------------------------------------
#                                                                                 slope
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-01-10")
def test_slope_improving_when_consumption_falls(converter):
    rows = [_row(date(2026, 1, day), 11 - day) for day in range(1, 11)]
    stats = TrendStats(converter, current_daily=rows)

    slope = stats.slope()

    assert slope.direction == "down"
    assert slope.improving is True
    assert slope.pct == 163.6
    assert slope.has_data is True


@time_machine.travel("2026-01-10")
def test_slope_worsening_when_consumption_rises(converter):
    rows = [_row(date(2026, 1, day), day) for day in range(1, 11)]
    stats = TrendStats(converter, current_daily=rows)

    slope = stats.slope()

    assert slope.direction == "up"
    assert slope.improving is False


@time_machine.travel("2026-01-05")
def test_slope_window_uses_only_recent_days(converter):
    # a big spike on day 1, then a small rising tail on days 4-5
    rows = [
        _row(date(2026, 1, 1), 100),
        _row(date(2026, 1, 4), 1),
        _row(date(2026, 1, 5), 2),
    ]
    stats = TrendStats(converter, current_daily=rows)

    # a 2-day window sees only the rising tail
    assert stats.slope(2).direction == "up"
    # the full window is dominated by the day-1 spike -> downward
    assert stats.slope(90).direction == "down"


@time_machine.travel("2026-01-01")
def test_slope_has_no_data_with_single_day(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 3)])

    slope = stats.slope()

    assert slope.has_data is False
    assert slope.direction == "flat"


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
