import json
from datetime import date

import pytest
import time_machine
from django.utils.translation import gettext as _

from ...lib.drinks_risk import RiskStats
from ...lib.drinks_stats import DataRow
from ...services import risk
from ...services.risk.builders import (
    RiskBuilder,
    RiskCardViewModel,
    RiskHeavyChartViewModel,
    RiskWeeklyChartViewModel,
)
from ...services.risk.providers import RiskDataProvider
from ..factories import DrinkFactory

pytestmark = pytest.mark.django_db


def _row(dt: date, stdav: float) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=0.0)


def _card(cards, title):
    return next(c for c in cards if c.title == title)


# -------------------------------------------------------------------------------------
#                                                                   weekly chart VM
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_chart_weekly_view_model():
    # 2026-01-05 is a Monday, so it is its own week's label
    stats = RiskStats(current_daily=[_row(date(2026, 1, 5), 7)])

    vm = RiskBuilder(stats).chart_weekly()

    assert isinstance(vm, RiskWeeklyChartViewModel)
    assert vm.low_risk == 11.2
    assert vm.high_risk == 28.0
    assert vm.data[vm.categories.index("2026-01-05")] == 7.0
    assert len(vm.categories) == len(vm.data)
    assert set(vm.text) == {"title", "unit", "weekly", "guideline"}


@time_machine.travel("2026-03-01")
def test_chart_weekly_as_dict_is_json_serializable():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 5), 7)])

    actual = RiskBuilder(stats).chart_weekly().as_dict
    serialized = json.loads(json.dumps(actual))

    assert serialized["low_risk"] == 11.2
    assert serialized["categories"][0] == "2025-12-29"


# -------------------------------------------------------------------------------------
#                                                                    heavy chart VM
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-12-31")
def test_chart_heavy_days_view_model():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 1), 7)])

    vm = RiskBuilder(stats).chart_heavy_days()

    assert isinstance(vm, RiskHeavyChartViewModel)
    assert len(vm.categories) == 12
    assert len(vm.data) == 12
    assert vm.data[0] == 1
    assert set(vm.text) == {"title", "unit", "heavy"}


@time_machine.travel("2026-12-31")
def test_chart_heavy_days_as_dict_is_json_serializable():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 1), 7)])

    actual = RiskBuilder(stats).chart_heavy_days().as_dict
    serialized = json.loads(json.dumps(actual))

    assert serialized["data"][0] == 1
    assert len(serialized["categories"]) == 12


# -------------------------------------------------------------------------------------
#                                                                          cards
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_get_cards_returns_four_view_models():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 5), 7)])

    cards = RiskBuilder(stats).get_cards()

    assert len(cards) == 4
    assert all(isinstance(c, RiskCardViewModel) for c in cards)
    assert [c.title for c in cards] == [
        _("This week"),
        _("Worst week"),
        _("Weeks over guideline"),
        _("Heavy days"),
    ]


@time_machine.travel("2026-02-11")
def test_this_week_card_low():
    stats = RiskStats(current_daily=[_row(date(2026, 2, 9), 3)])

    card = _card(RiskBuilder(stats).get_cards(), _("This week"))

    assert card.state == "low"
    assert card.value == "3.0"
    assert card.show_icon is False


@time_machine.travel("2026-02-11")
def test_this_week_card_high():
    stats = RiskStats(current_daily=[_row(date(2026, 2, 9), 30)])

    card = _card(RiskBuilder(stats).get_cards(), _("This week"))

    assert card.state == "high"


@time_machine.travel("2026-03-01")
def test_worst_week_card_empty_without_data():
    card = _card(RiskBuilder(RiskStats(current_daily=[])).get_cards(), _("Worst week"))

    assert card.state == "empty"
    assert card.value == ""


@time_machine.travel("2026-03-01")
def test_worst_week_card_high():
    stats = RiskStats(current_daily=[_row(date(2026, 2, 9), 30)])

    card = _card(RiskBuilder(stats).get_cards(), _("Worst week"))

    assert card.state == "high"
    assert card.value == "30.0"


@time_machine.travel("2026-06-01")
def test_count_card_improving():
    current = [_row(date(2026, 1, 1), 7)]
    past = [_row(date(2025, 1, 1), 7), _row(date(2025, 2, 1), 8)]

    card = _card(
        RiskBuilder(RiskStats(current_daily=current, past_daily=past)).get_cards(),
        _("Heavy days"),
    )

    assert card.state == "improving"
    assert card.show_icon is True
    assert card.value == "1"
    assert card.note == "1 / 2"


@time_machine.travel("2026-06-01")
def test_count_card_worsening():
    current = [_row(date(2026, 1, 1), 7), _row(date(2026, 2, 1), 8)]
    past = [_row(date(2025, 1, 1), 7)]

    card = _card(
        RiskBuilder(RiskStats(current_daily=current, past_daily=past)).get_cards(),
        _("Heavy days"),
    )

    assert card.state == "worsening"


@time_machine.travel("2026-06-01")
def test_count_card_neutral_without_past():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 1), 7)])

    card = _card(RiskBuilder(stats).get_cards(), _("Heavy days"))

    assert card.state == "neutral"
    assert card.show_icon is False
    assert card.value == "1"


# -------------------------------------------------------------------------------------
#                                                                RiskDataProvider
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_provider_fetches_current_and_past_daily(main_user):
    DrinkFactory(user=main_user, date=date(2026, 1, 10), stdav=3)
    DrinkFactory(user=main_user, date=date(2025, 1, 10), stdav=2)

    data = RiskDataProvider(main_user, 2026).get_data()

    assert len(data.current_daily) == 1
    assert len(data.past_daily) == 1
    assert data.current_daily[0]["date"] == date(2026, 1, 10)


# -------------------------------------------------------------------------------------
#                                                                     load_service
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_load_service_returns_cards_and_charts(main_user):
    DrinkFactory(user=main_user, date=date(2026, 1, 10), stdav=7)

    result = risk.load_service(main_user, 2026)

    assert set(result) == {"cards", "chart_weekly", "chart_heavy"}
    assert len(result["cards"]) == 4
    assert isinstance(result["chart_weekly"], RiskWeeklyChartViewModel)


@time_machine.travel("2026-03-01")
def test_load_service_handles_no_data(main_user):
    result = risk.load_service(main_user, 2026)

    # 2026-01-01 falls in the week starting Mon 2025-12-29; 2026-03-01 falls in
    # the week starting Mon 2026-02-23 -> 9 dense weekly buckets, all empty
    assert len(result["cards"]) == 4
    assert result["chart_weekly"].data == [0.0] * 9
