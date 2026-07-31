import re
from datetime import date

import pytest
import time_machine
from django.conf import settings
from django.utils.translation import gettext as _

from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DataRow
from ...lib.drinks_trend import (
    TrendStats,
)
from ...services.stat_card import StatCard
from ...services.trends_tab import (
    TrendChartViewModel,
    TrendsBuilder,
    TrendsTab,
)
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
    assert set(actual.text) == {"daily", "r7", "r30", "limit", "title", "unit"}
    assert actual.text["unit"] == "ml"


@time_machine.travel("2026-01-05")
def test_chart_trend_carries_unaveraged_daily_volume(converter):
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 5)])

    actual = TrendsBuilder(stats, target=250).chart_trend()

    # raw ml/day, one point per category: 5 std av * 200 ml beer on Jan 1 only
    assert len(actual.daily) == len(actual.categories)
    assert actual.daily == [1000, 0, 0, 0, 0]
    assert actual.text["daily"] == _("Per day")


@time_machine.travel("2026-01-05")
def test_chart_trend_unit_follows_the_selected_drink_type():
    """The chart is labelled in whatever unit the drink-type dropdown selects."""
    rows = [_row(date(2026, 1, 1), 5)]

    beer = TrendsBuilder(TrendStats(DrinkConverter("beer"), rows)).chart_trend()
    std_av = TrendsBuilder(TrendStats(DrinkConverter("stdav"), rows)).chart_trend()

    assert beer.text["unit"] == "ml"
    assert std_av.text["unit"] == "Std Av"
    # ... and the series are in that unit, so the Limit line stays comparable
    assert beer.daily[0] == 1000
    assert std_av.daily[0] == 5
    # a whole ml is precise enough; rounding Std Av that far would erase it,
    # flattening a 2.2 average and a 1.5 target onto the same tick
    assert beer.decimals == 0
    assert std_av.decimals == 1
    assert std_av.rolling_7[0] == round(5 / 7, 1)


@time_machine.travel("2026-01-05")
def test_chart_trend_payload_matches_the_keys_its_script_reads(converter):
    """The view model exists only to feed chart_drinks_trend.js.

    A key the script reads but the builder never sends renders as ``undefined``
    in the browser and no Python test would notice, so the two are pinned to
    each other in both directions.
    """
    stats = TrendStats(converter, current_daily=[_row(date(2026, 1, 1), 5)])
    payload = TrendsBuilder(stats, target=250).chart_trend().as_dict

    source = (settings.SITE_ROOT / "static" / "js" / "chart_drinks_trend.js").read_text(
        encoding="utf-8"
    )

    assert set(re.findall(r"chartData\.(\w+)", source)) == set(payload)
    assert set(re.findall(r"chartData\.text\.(\w+)", source)) == set(payload["text"])


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
    assert set(actual.text) == {"this_year", "last_year", "target", "title", "unit"}
    assert actual.text["unit"] == "L"


@time_machine.travel("2026-01-05")
def test_chart_cumulative_counts_std_av_instead_of_bottling_it():
    """A year of Std Av is a count, so it is never divided into litres."""
    stats = TrendStats(
        DrinkConverter("stdav"),
        current_daily=[_row(date(2026, 1, 1), 5)],
        past_daily=[_row(date(2025, 1, 1), 2)],
        target=1.5,
    )

    actual = TrendsBuilder(stats, target=1.5).chart_cumulative()

    assert actual.text["unit"] == "Std Av"
    assert actual.this_year[0] == 5.0  # 5 Std Av, not 0.05 L
    assert actual.last_year[0] == 2.0
    assert actual.target[0] == 1.5


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
    assert all(isinstance(c, StatCard) for c in cards)
    assert [c.title for c in cards] == [
        _("Trend (2 weeks)"),
        _("Trend (month)"),
        _("Trend (90 days)"),
        _("This year vs last (to date)"),
        _("Year-end forecast"),
    ]


# -------------------------------------------------------------------------------------
#                                                                        TrendsTab.build
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_trends_tab_build_returns_charts_and_cards(main_user):
    DrinkFactory(user=main_user, date=date(2026, 1, 10), stdav=3)
    DrinkFactory(user=main_user, date=date(2025, 1, 10), stdav=2)

    result = TrendsTab.build(main_user, 2026)

    assert set(result) == {"chart_trend", "chart_cumulative", "cards"}
    assert len(result["cards"]) == 5


@time_machine.travel("2026-03-01")
def test_trends_tab_build_reads_target(main_user):
    DrinkTargetFactory(user=main_user, year=2026, quantity=100)

    result = TrendsTab.build(main_user, 2026)

    assert result["chart_trend"].target == 100.0
