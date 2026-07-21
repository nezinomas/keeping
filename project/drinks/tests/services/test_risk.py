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
    assert vm.heavy_threshold == 6.0
    assert set(vm.text) == {"title", "unit", "heavy", "threshold_label"}


@time_machine.travel("2026-12-31")
def test_chart_heavy_days_as_dict_is_json_serializable():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 1), 7)])

    actual = RiskBuilder(stats).chart_heavy_days().as_dict
    serialized = json.loads(json.dumps(actual))

    assert serialized["data"][0] == 1
    assert len(serialized["categories"]) == 12
    assert serialized["heavy_threshold"] == 6.0


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
    # weeks over the 11.2 std av guideline: 1 this year vs 2 last year
    current = [_row(date(2026, 1, 5), 15)]
    past = [_row(date(2025, 1, 6), 15), _row(date(2025, 2, 3), 20)]

    card = _card(
        RiskBuilder(RiskStats(current_daily=current, past_daily=past)).get_cards(),
        _("Weeks over guideline"),
    )

    assert card.state == "improving"
    assert card.show_icon is True
    assert card.value == "1"
    assert card.note == "1 / 2"


@time_machine.travel("2026-06-01")
def test_count_card_worsening():
    current = [_row(date(2026, 1, 5), 15), _row(date(2026, 2, 2), 20)]
    past = [_row(date(2025, 1, 6), 15)]

    card = _card(
        RiskBuilder(RiskStats(current_daily=current, past_daily=past)).get_cards(),
        _("Weeks over guideline"),
    )

    assert card.state == "worsening"


@time_machine.travel("2026-06-01")
def test_count_card_neutral_without_past():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 5), 15)])

    card = _card(RiskBuilder(stats).get_cards(), _("Weeks over guideline"))

    assert card.state == "neutral"
    assert card.show_icon is False
    assert card.value == "1"


# -------------------------------------------------------------------------------------
#                                                        count card explanation text
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-06-01")
def test_heavy_days_explanation_holds_threshold_and_comparison():
    current = [_row(date(2026, 1, 1), 7)]
    past = [_row(date(2025, 1, 1), 7), _row(date(2025, 2, 1), 8)]

    card = _card(
        RiskBuilder(RiskStats(current_daily=current, past_daily=past)).get_cards(),
        _("Heavy days"),
    )

    # the descriptive text lives in the collapsible explanation, not the note
    assert card.note == "1 / 2"
    assert "6" in card.explanation
    assert "Std Av" in card.explanation
    expected = (
        _("Days with more than %(threshold)s Std Av in a single day.")
        % {"threshold": "6"}
        + " "
        + _("The two numbers are this year and last year, up to the same date.")
    )
    assert card.explanation == expected


@time_machine.travel("2026-06-01")
def test_weeks_over_explanation_holds_guideline():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 5), 15)])

    card = _card(RiskBuilder(stats).get_cards(), _("Weeks over guideline"))

    # no prior year -> explanation is the definition only (no comparison sentence)
    assert card.note == _("No prior year")
    assert "11.2" in card.explanation
    assert card.explanation == _(
        "Weeks whose total exceeds the low-risk guideline of %(threshold)s Std Av."
    ) % {"threshold": "11.2"}


@time_machine.travel("2026-06-01")
def test_zone_cards_have_no_explanation():
    # This week / Worst week are levels, not comparisons -> no collapsible
    cards = RiskBuilder(
        RiskStats(current_daily=[_row(date(2026, 1, 5), 5)])
    ).get_cards()

    assert _card(cards, _("This week")).explanation == ""
    assert _card(cards, _("Worst week")).explanation == ""


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
