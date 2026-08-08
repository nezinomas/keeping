import json
from datetime import date

import pytest
import time_machine
from django.utils.translation import gettext as _

from ....core.lib.stat_card import StatCard
from ...lib.drinks_risk import (
    HEAVY_DAY_STDAV,
    WEEKLY_HIGH_RISK_STDAV,
    WEEKLY_LOW_RISK_STDAV,
    RiskStats,
)
from ...lib.drinks_stats import DataRow
from ...services.risk_tab import (
    MonthlyHeavyDaysChartViewModel,
    RiskTab,
    RiskViewModelBuilder,
    WeeklyRiskChartViewModel,
)
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

    vm = RiskViewModelBuilder(stats).chart_weekly()

    assert isinstance(vm, WeeklyRiskChartViewModel)
    assert vm.low_risk == 11.2
    assert vm.high_risk == 28.0
    index = vm.categories.index("2026-01-05")
    assert vm.data[index] == 7.0
    assert vm.week_ends[index] == "2026-01-11"  # Sunday of that week
    assert len(vm.categories) == len(vm.data) == len(vm.week_ends)
    assert set(vm.text) == {
        "title",
        "unit",
        "weekly",
        "guideline",
        "high_risk_guideline",
    }


@time_machine.travel("2026-03-01")
def test_chart_weekly_as_dict_is_json_serializable():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 5), 7)])

    actual = RiskViewModelBuilder(stats).chart_weekly().as_dict
    serialized = json.loads(json.dumps(actual))

    assert serialized["low_risk"] == 11.2
    assert serialized["categories"][0] == "2025-12-29"
    assert serialized["week_ends"][0] == "2026-01-04"


# -------------------------------------------------------------------------------------
#                                                                    heavy chart VM
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-12-31")
def test_chart_heavy_days_view_model():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 1), 7)])

    vm = RiskViewModelBuilder(stats).chart_heavy_days()

    assert isinstance(vm, MonthlyHeavyDaysChartViewModel)
    assert len(vm.categories) == 12
    assert len(vm.data) == 12
    assert vm.data[0] == 1
    assert vm.heavy_threshold == 6.0
    # every Heavy day is harm, so the chart carries no guideline to cross
    assert not hasattr(vm, "low_risk")
    assert not hasattr(vm, "high_risk")
    assert set(vm.text) == {"title", "unit", "heavy", "threshold_label"}


@time_machine.travel("2026-12-31")
def test_chart_heavy_days_as_dict_is_json_serializable():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 1), 7)])

    actual = RiskViewModelBuilder(stats).chart_heavy_days().as_dict
    serialized = json.loads(json.dumps(actual))

    assert serialized["data"][0] == 1
    assert len(serialized["categories"]) == 12
    assert serialized["heavy_threshold"] == 6.0
    assert "low_risk" not in serialized
    assert "high_risk" not in serialized


# -------------------------------------------------------------------------------------
#                                                                          cards
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_get_cards_returns_four_view_models():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 5), 7)])

    cards = RiskViewModelBuilder(stats).get_cards()

    assert len(cards) == 4
    assert all(isinstance(c, StatCard) for c in cards)
    assert [c.title for c in cards] == [
        _("This week"),
        _("Worst week"),
        _("Weeks over guideline"),
        _("Heavy days"),
    ]


@time_machine.travel("2026-02-11")
def test_this_week_card_low():
    stats = RiskStats(current_daily=[_row(date(2026, 2, 9), 3)])

    card = _card(RiskViewModelBuilder(stats).get_cards(), _("This week"))

    assert card.state == "low"
    assert card.value == "3.0"
    assert card.show_icon is False
    # inside the guideline is the baseline, so there is no crossing to name
    assert card.state_label == ""


@time_machine.travel("2026-02-11")
def test_this_week_card_high():
    stats = RiskStats(current_daily=[_row(date(2026, 2, 9), 30)])

    card = _card(RiskViewModelBuilder(stats).get_cards(), _("This week"))

    assert card.state == "high"
    assert card.state_label == _("Over the high-risk threshold")


@time_machine.travel("2026-02-11")
def test_this_week_card_medium_names_the_band_it_crossed():
    stats = RiskStats(current_daily=[_row(date(2026, 2, 9), 15)])

    card = _card(RiskViewModelBuilder(stats).get_cards(), _("This week"))

    assert card.state == "medium"
    assert card.state_label == _("Over the low-risk guideline")


@time_machine.travel("2026-03-01")
def test_worst_week_card_empty_without_data():
    card = _card(
        RiskViewModelBuilder(RiskStats(current_daily=[])).get_cards(), _("Worst week")
    )

    assert card.state == "empty"
    assert card.value == ""


@time_machine.travel("2026-03-01")
def test_worst_week_card_high():
    stats = RiskStats(current_daily=[_row(date(2026, 2, 9), 30)])

    card = _card(RiskViewModelBuilder(stats).get_cards(), _("Worst week"))

    assert card.state == "high"
    assert card.value == "30.0"
    assert card.state_label == _("Over the high-risk threshold")
    # note shows the full week range: Monday – Sunday
    assert card.note == "2026-02-09 – 2026-02-15"


@time_machine.travel("2026-06-01")
def test_count_card_improving():
    # weeks over the 11.2 std av guideline: 1 this year vs 2 last year
    current = [_row(date(2026, 1, 5), 15)]
    past = [_row(date(2025, 1, 6), 15), _row(date(2025, 2, 3), 20)]

    card = _card(
        RiskViewModelBuilder(
            RiskStats(current_daily=current, past_daily=past)
        ).get_cards(),
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
        RiskViewModelBuilder(
            RiskStats(current_daily=current, past_daily=past)
        ).get_cards(),
        _("Weeks over guideline"),
    )

    assert card.state == "worsening"


@time_machine.travel("2026-06-01")
def test_count_card_neutral_without_past():
    stats = RiskStats(current_daily=[_row(date(2026, 1, 5), 15)])

    card = _card(RiskViewModelBuilder(stats).get_cards(), _("Weeks over guideline"))

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
        RiskViewModelBuilder(
            RiskStats(current_daily=current, past_daily=past)
        ).get_cards(),
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

    card = _card(RiskViewModelBuilder(stats).get_cards(), _("Weeks over guideline"))

    # no prior year -> explanation is the definition only (no comparison sentence)
    assert card.note == _("No prior year")
    assert "11.2" in card.explanation
    assert card.explanation == _(
        "Weeks whose total exceeds the low-risk guideline of %(threshold)s Std Av."
    ) % {"threshold": "11.2"}


@time_machine.travel("2026-06-01")
def test_zone_cards_have_no_explanation():
    # This week / Worst week are levels, not comparisons -> no collapsible
    cards = RiskViewModelBuilder(
        RiskStats(current_daily=[_row(date(2026, 1, 5), 5)])
    ).get_cards()

    assert _card(cards, _("This week")).explanation == ""
    assert _card(cards, _("Worst week")).explanation == ""


# -------------------------------------------------------------------------------------
#                                                                         RiskTab.build
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-03-01")
def test_risk_tab_build_returns_cards_and_charts(main_user):
    DrinkFactory(user=main_user, date=date(2026, 1, 10), stdav=7)
    DrinkFactory(user=main_user, date=date(2025, 1, 10), stdav=2)

    result = RiskTab.build(main_user, 2026)

    assert set(result) == {"cards", "chart_weekly", "chart_heavy"}
    assert len(result["cards"]) == 4
    assert isinstance(result["chart_weekly"], WeeklyRiskChartViewModel)


@time_machine.travel("2026-03-01")
def test_risk_tab_build_handles_no_data(main_user):
    result = RiskTab.build(main_user, 2026)

    assert len(result["cards"]) == 4
    assert result["chart_weekly"].data == [0.0] * 9


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
@time_machine.travel("2026-03-01")
def test_risk_tab_build_is_the_same_tab_under_every_drink_type(drink_type, main_user):
    """Nothing on this tab follows the drink-type dropdown.

    Every figure here is read against a guideline defined in Std Av, so
    converting any of them would leave the plot lines and the band colours
    marking levels the data no longer measures.

    As on the Habits tab, this has to be asserted against ``build`` rather than
    ``RiskViewModelBuilder``: the builder is handed a ``RiskStats`` and never
    sees a drink type, so a test parametrizing one at that layer cannot fail.
    ``build`` is where it arrives — ``ConsumptionYear`` annotates ``DataRow.qty``
    off ``user.drink_type``.
    """
    main_user.drink_type = drink_type
    DrinkFactory(user=main_user, date=date(2026, 2, 9), stdav=15)  # a Monday

    result = RiskTab.build(main_user, 2026)
    weekly, heavy = result["chart_weekly"], result["chart_heavy"]

    # the week keeps its Std Av total, and the guidelines it is banded against
    assert weekly.data[weekly.categories.index("2026-02-09")] == 15.0
    assert weekly.low_risk == WEEKLY_LOW_RISK_STDAV
    assert weekly.high_risk == WEEKLY_HIGH_RISK_STDAV
    assert weekly.text["unit"] == "Std Av"

    # 15 Std Av in one day is over the Heavy day threshold, in February
    assert heavy.data[1] == 1
    assert heavy.heavy_threshold == HEAVY_DAY_STDAV

    cards = result["cards"]
    assert _card(cards, _("Worst week")).value == "15.0"
    assert _card(cards, _("Worst week")).state == "medium"
    assert _card(cards, _("Heavy days")).value == "1"
    assert _card(cards, _("Weeks over guideline")).value == "1"
