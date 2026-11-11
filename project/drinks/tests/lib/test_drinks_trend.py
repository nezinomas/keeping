from datetime import date

import pytest

from ...lib.daily_limit import DailyLimit
from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DataRow
from ...lib.drinks_trend import TrendStats


@pytest.fixture(name="converter")
def fixture_converter():
    return DrinkConverter("beer")


def _row(dt: date, stdav: float) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=0.0)


def test_categories_span_from_jan_first_to_today(converter):
    stats = TrendStats(converter, current_daily=[], year=2026, today=date(2026, 3, 1))

    # 2026 is not a leap year: 31 (Jan) + 28 (Feb) + 1 = 60
    assert len(stats.date_labels) == 60
    assert stats.date_labels[0] == "2026-01-01"
    assert stats.date_labels[-1] == "2026-03-01"


def test_past_year_spans_full_year(converter):
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2025, 5, 5), 1)],
        year=2025,
        today=date(2026, 6, 15),
    )

    assert len(stats.date_labels) == 365
    assert stats.date_labels[0] == "2025-01-01"
    assert stats.date_labels[-1] == "2025-12-31"


def test_rolling_average_divides_by_full_window(converter):
    # beer: 1 stdav -> 200 ml, so 5 stdav -> 1000 ml on the first day only
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 1), 5)],
        year=2026,
        today=date(2026, 1, 5),
    )

    # every point divides by the FULL window (no start-of-year spike from a
    # short denominator); the 1000 ml day stays inside both windows for Jan 1-5
    assert stats.calculate_rolling_average(7) == pytest.approx([1000 / 7] * 5)
    assert stats.calculate_rolling_average(30) == pytest.approx([1000 / 30] * 5)


@pytest.mark.parametrize(
    "drink_type, expected",
    [
        # never scaled into the 10 ml of pure alcohol one Std Av holds, which would
        # put the series 10x above the Drink Target it is read against
        pytest.param("stdav", (5 / 7, 5), id="std_av_as_typed"),
        pytest.param("beer", (1000 / 7, 1000), id="a_volume_drink_type_in_ml"),
    ],
)
def test_rolling_average_shows_the_drink_types_unit(drink_type, expected):
    stats = TrendStats(
        DrinkConverter(drink_type),
        current_daily=[_row(date(2026, 1, 1), 5)],
        year=2026,
        today=date(2026, 1, 5),
    )

    actual = (stats.calculate_rolling_average(7)[0], stats.daily_volume[0])

    assert actual == pytest.approx(expected)


def test_rolling_average_seeds_from_previous_december(converter):
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 1), 5)],  # 1000 ml
        past_daily=[_row(date(2025, 12, 31), 5)],  # 1000 ml, inside the window
        year=2026,
        today=date(2026, 1, 2),
    )

    # Jan 1's 7-day mean pulls in Dec 31 -> (1000 + 1000) / 7
    assert stats.calculate_rolling_average(7)[0] == pytest.approx(2000 / 7)


@pytest.mark.parametrize(
    "recent, prior, change, improving",
    [
        pytest.param(3, 9, 66.7, True, id="lower"),  # abs(3 - 9) / 9 * 100
        pytest.param(10, 2, 400.0, False, id="higher"),  # abs(10 - 2) / 2 * 100
    ],
)
def test_period_compares_the_recent_window_with_the_one_before(
    converter, recent, prior, change, improving
):
    # last 14 days (Jan 18 - Feb 1), prior 14 days (Jan 4 - Jan 18)
    rows = [_row(date(2026, 1, 25), recent), _row(date(2026, 1, 10), prior)]
    stats = TrendStats(converter, current_daily=rows, year=2026, today=date(2026, 2, 1))

    p = stats.compare_recent_period(14)

    assert (p.current_period_average, p.previous_period_average) == (recent, prior)
    assert p.percentage_change == change
    assert p.improving is improving
    assert p.has_data is True


def test_period_without_prior_baseline(converter):
    # only recent drinking, nothing in the previous window -> no percentage
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 15), 4)],
        year=2026,
        today=date(2026, 1, 20),
    )

    p = stats.compare_recent_period(14)

    assert p.current_period_average == 4
    assert p.previous_period_average == 0.0
    assert p.percentage_change == 0.0
    assert p.has_data is True


def test_period_no_data(converter):
    stats = TrendStats(converter, current_daily=[], year=2026, today=date(2026, 6, 1))

    assert stats.compare_recent_period(14).has_data is False


def test_period_straddles_year_boundary(converter):
    # prior window reaches into last December -> must use previous-year data
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 10), 2)],
        past_daily=[_row(date(2025, 12, 30), 8)],
        year=2026,
        today=date(2026, 1, 20),
    )

    p = stats.compare_recent_period(14)

    assert p.current_period_average == 2
    assert p.previous_period_average == 8
    assert p.improving is True


def test_ytd_vs_last_year(converter):
    current = [_row(date(2026, 1, 1), 10), _row(date(2026, 2, 1), 5)]
    past = [
        _row(date(2025, 1, 1), 20),
        _row(date(2025, 4, 10), 100),  # after today's month and day, left out
    ]
    stats = TrendStats(
        converter,
        current_daily=current,
        past_daily=past,
        year=2026,
        today=date(2026, 3, 1),
    )

    ytd = stats.compare_year_to_date()

    assert ytd.current_year_average == 15
    assert ytd.previous_year_average == 20
    assert (
        ytd.percentage_change == 25.0
    )  # magnitude; direction is carried by `improving`
    assert ytd.improving is True
    assert ytd.has_past is True


def test_ytd_without_past_data(converter):
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 1), 10)],
        year=2026,
        today=date(2026, 3, 1),
    )

    ytd = stats.compare_year_to_date()

    assert ytd.current_year_average == 10
    assert ytd.has_past is False
    assert ytd.percentage_change == 0.0


@pytest.mark.parametrize(
    "current, past, expected",
    [
        pytest.param(
            [],
            [_row(date(2024, 2, 29), 1), _row(date(2024, 3, 1), 2)],
            (0, 3),
            id="last_year_after_a_leap_year",
        ),
        pytest.param(
            [_row(date(2025, 3, 1), 1), _row(date(2025, 3, 2), 2)],
            [_row(date(2024, 1, 1), 4)],
            (1, 4),
            id="this_year_to_today",
        ),
    ],
)
def test_ytd_reads_each_year_to_the_same_month_and_day(current, past, expected):
    stats = TrendStats(
        DrinkConverter("stdav"),
        current_daily=current,
        past_daily=past,
        year=2025,
        today=date(2025, 3, 1),
    )
    ytd = stats.compare_year_to_date()

    assert (ytd.current_year_average, ytd.previous_year_average) == expected


def _steps(series: list[float]) -> tuple[int, dict[int, float]]:
    """The series' length and each index its total changes at: the whole line, read
    without a 365-item diff."""
    changes = {i: v for i, v in enumerate(series) if i == 0 or v != series[i - 1]}
    return len(series), changes


# index 58 is Feb 28, 59 is Mar 1 of a common year and Feb 29 of a leap one
@pytest.mark.parametrize(
    "year, past, expected",
    [
        pytest.param(
            2025,
            [_row(date(2024, 3, 1), 1), _row(date(2024, 12, 31), 2)],
            (365, {0: 0.0, 59: 1.0, 364: 3.0}),
            id="after_a_leap_year_mar_1_and_dec_31_keep_their_days",
        ),
        pytest.param(
            2025,
            [_row(date(2024, 2, 29), 1)],
            (365, {0: 0.0, 58: 1.0}),
            id="after_a_leap_year_feb_29_folds_into_feb_28",
        ),
        pytest.param(
            2025,
            [_row(date(2024, 2, 28), 1), _row(date(2024, 2, 29), 2)],
            (365, {0: 0.0, 58: 3.0}),
            id="after_a_leap_year_feb_28_and_29_add_up",
        ),
        pytest.param(
            2024,
            [_row(date(2023, 2, 28), 1), _row(date(2023, 3, 1), 2)],
            (366, {0: 0.0, 58: 1.0, 60: 3.0}),
            id="in_a_leap_year_feb_29_has_no_last_year_day",
        ),
    ],
)
def test_cumulative_past_year_matches_days_by_month_and_day(year, past, expected):
    stats = TrendStats(
        DrinkConverter("stdav"),
        past_daily=past,
        year=year,
        today=date(2026, 6, 15),
    )

    assert _steps(stats.cumulative_past_year) == expected


@pytest.mark.parametrize(
    "drink_type, daily_target, expected",
    [
        # 10 std av -> 2000 ml over 10 days = 200 ml/day, * 365 / 1000
        pytest.param("beer", 100, ("L", 73.0, 36.5), id="beer_in_litres"),
        # the forecast and its target share one unit: 1/day * 365, not 3650
        pytest.param("stdav", 0.5, ("Std Av", 365.0, 182.5), id="std_av_as_typed"),
    ],
)
def test_projection_over_target(drink_type, daily_target, expected):
    stats = TrendStats(
        DrinkConverter(drink_type),
        current_daily=[_row(date(2026, 1, 1), 10)],
        limit=DailyLimit(daily_target),
        year=2026,
        today=date(2026, 1, 10),
    )

    projection = stats.calculate_projection()

    assert (
        stats.total_unit,
        projection.projected_total,
        projection.target_total,
    ) == expected
    assert projection.percentage_difference == 100.0
    assert projection.over is True
    assert projection.has_target is True


def test_projection_without_target(converter):
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 1), 10)],
        year=2026,
        today=date(2026, 1, 10),
    )

    projection = stats.calculate_projection()

    assert projection.has_target is False
    assert projection.percentage_difference == 0.0


def test_a_coming_year_draws_no_line_on_its_own_calendar(converter):
    stats = TrendStats(
        converter,
        year=2027,
        current_daily=[_row(date(2027, 1, 2), 5)],
        past_daily=[_row(date(2026, 1, 1), 5)],
        today=date(2026, 11, 3),
    )

    assert stats.cumulative_current_year == []
    assert stats.daily_volume == []
    assert len(stats.date_labels) == 365
    assert stats.calculate_rolling_average(7) == []
    assert len(stats.cumulative_categories) == 365


def test_a_coming_year_has_no_recent_period(converter):
    # dated late in the year, so a window ending Dec 31 would reach it
    stats = TrendStats(
        converter,
        year=2027,
        current_daily=[_row(date(2027, 12, 20), 5)],
        today=date(2026, 11, 3),
    )

    assert stats.compare_recent_period(14).has_data is False


def test_current_year_is_the_year_the_caller_views(converter):
    stats = TrendStats(
        converter,
        year=2027,
        current_daily=[],
        past_daily=[_row(date(2026, 1, 1), 5)],
        today=date(2026, 8, 3),
    )

    assert stats.current_year == 2027
    assert stats.date_labels[0] == "2027-01-01"
    assert stats.cumulative_categories[0] == "2027-01-01"
