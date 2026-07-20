from datetime import date

import pytest
import time_machine

from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_trend import ProjectionStats, SlopeStats, TrendStats, YtdStats
from ...services.trends.builders import (
    TrendChartViewModel,
    TrendItemViewModel,
    TrendsBuilder,
)
from ...services.trends.providers import TrendsDataProvider
from ..factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(name="converter")
def fixture_converter():
    return DrinkConverter("beer")


def _row(dt: date, stdav: float) -> dict:
    return {"date": dt, "stdav": stdav, "qty": 0.0}


# -------------------------------------------------------------------------------------
#                                                                       TrendsBuilder
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-01-05")
def test_chart_trend_view_model(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 5)])
    builder = TrendsBuilder(stats, target=250)

    actual = builder.chart_trend()

    assert isinstance(actual, TrendChartViewModel)
    assert actual.categories[0] == "2026-01-01"
    assert len(actual.categories) == 5
    assert len(actual.rolling_7) == 5
    assert len(actual.rolling_30) == 5
    assert actual.rolling_7[0] == 1000
    assert actual.target == 250
    assert set(actual.text) == {"r7", "r30", "limit"}


@time_machine.travel("2026-01-05")
def test_chart_trend_target_is_none_when_zero(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 5)])

    actual = TrendsBuilder(stats, target=0).chart_trend()

    assert actual.target is None


@time_machine.travel("2026-01-05")
def test_chart_trend_as_dict_is_json_serializable(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 5)])

    actual = TrendsBuilder(stats, target=250).chart_trend().as_dict

    assert actual["categories"][0] == "2026-01-01"
    assert actual["rolling_30"][0] == 1000
    assert actual["target"] == 250


@time_machine.travel("2026-03-01")
def test_builder_passes_through_stats(converter):
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 1), 10)],
        past_daily=[_row(date(2025, 1, 1), 20)],
        target=100,
    )
    builder = TrendsBuilder(stats, target=100)

    assert isinstance(builder.trend_ytd(), YtdStats)
    assert isinstance(builder.trend_projection(), ProjectionStats)


@time_machine.travel("2026-03-01")
def test_trend_items_cover_three_windows(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 10)])

    items = TrendsBuilder(stats).trend_items()

    assert len(items) == 3
    assert all(isinstance(i, TrendItemViewModel) for i in items)
    assert all(isinstance(i.slope, SlopeStats) for i in items)
    assert [i.title for i in items] == [
        "Tendencija (2 savaitės)",
        "Tendencija (mėnuo)",
        "Tendencija (90 dienų)",
    ]


# -------------------------------------------------------------------------------------
#                                                                  TrendsDataProvider
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_provider_fetches_current_and_past_daily(main_user):
    DrinkFactory(user=main_user, date=date(2026, 1, 10), stdav=3)
    DrinkFactory(user=main_user, date=date(2025, 1, 10), stdav=2)

    data = TrendsDataProvider(main_user, 2026).get_data()

    assert len(data.current_daily) == 1
    assert len(data.past_daily) == 1
    assert data.current_daily[0]["date"] == date(2026, 1, 10)
    assert data.past_daily[0]["date"] == date(2025, 1, 10)


@time_machine.travel("2026-03-01")
def test_provider_reads_target(main_user):
    DrinkTargetFactory(user=main_user, year=2026, quantity=100)

    data = TrendsDataProvider(main_user, 2026).get_data()

    assert data.target


@time_machine.travel("2026-03-01")
def test_provider_target_defaults_to_zero(main_user):
    data = TrendsDataProvider(main_user, 2026).get_data()

    assert data.target == 0.0
