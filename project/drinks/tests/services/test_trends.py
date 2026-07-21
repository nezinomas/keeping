from datetime import date

import pytest
import time_machine
from django.utils.translation import gettext as _

from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DataRow
from ...lib.drinks_trend import (
    TrendStats,
)
from ...services.trends.builders import (
    TrendCardViewModel,
    TrendChartViewModel,
    TrendsBuilder,
)
from ...services.trends.providers import TrendsDataProvider
from ..factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(name="converter")
def fixture_converter():
    return DrinkConverter("beer")


def _row(dt: date, stdav: float) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=0.0)


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
    assert actual.rolling_7[0] == round(1000 / 7)  # full-window mean, rounded
    assert actual.target == 250
    assert set(actual.text) == {"r7", "r30", "limit"}


@time_machine.travel("2026-01-05")
def test_chart_trend_target_is_zero(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 5)])

    actual = TrendsBuilder(stats, target=0.0).chart_trend()

    assert actual.target == 0.0


@time_machine.travel("2026-01-05")
def test_chart_cumulative_view_model(converter):
    stats = TrendStats(
        converter,
        current_daily=[_row(date(2026, 1, 1), 5)],
        past_daily=[_row(date(2025, 1, 1), 2)],
        target=1000,
    )
    builder = TrendsBuilder(stats, target=1000)

    actual = builder.chart_cumulative()

    assert actual.categories[0] == "2026-01-01"
    assert actual.categories[-1] == "2026-12-31"
    assert len(actual.categories) == 365
    assert len(actual.this_year) == 5
    assert len(actual.last_year) == 365
    assert len(actual.target) == 365
    # series are cumulative litres (ml / 1000), scaled by the selected drink type
    assert actual.this_year[0] == 1.0  # 5 std av * 200 ml beer = 1000 ml = 1.0 L
    assert actual.last_year[0] == 0.4  # 2 std av * 200 ml beer = 400 ml = 0.4 L
    assert actual.target[0] == 1.0  # 1000 ml/day target = 1.0 L cumulative on day 1
    assert set(actual.text) == {"this_year", "last_year", "target"}


@time_machine.travel("2026-01-05")
def test_chart_trend_as_dict_is_json_serializable(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 5)])

    actual = TrendsBuilder(stats, target=250).chart_trend().as_dict

    assert actual["categories"][0] == "2026-01-01"
    assert actual["rolling_30"][0] == round(1000 / 30)
    assert actual["target"] == 250


@time_machine.travel("2026-03-01")
def test_builder_get_cards(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 10)])
    cards = TrendsBuilder(stats).get_cards()

    assert len(cards) == 5
    assert all(isinstance(c, TrendCardViewModel) for c in cards)
    assert [c.title for c in cards] == [
        _("Trend (2 weeks)"),
        _("Trend (month)"),
        _("Trend (90 days)"),
        _("This year vs last (to date)"),
        _("Year-end forecast"),
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
