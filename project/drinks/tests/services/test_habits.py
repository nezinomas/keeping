from datetime import date

import pytest
import time_machine
from django.utils.translation import gettext as _

from ....core.lib.stat_card import StatCard
from ...lib.drinks_frequency import FrequencyStats
from ...lib.drinks_risk import HEAVY_DAY_STDAV
from ...lib.drinks_stats import DataRow
from ...services.habits_tab import HabitsBuilder, HabitsTab, WeekdayChartViewModel
from ..factories import DrinkFactory

pytestmark = pytest.mark.django_db


def _row(dt: date, stdav: float, qty: float = 0.0) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=qty)


def _builder(current=(), past=(), today=date(1999, 1, 19)) -> HabitsBuilder:
    return HabitsBuilder(
        FrequencyStats(current_daily=current, past_daily=past, today=today)
    )


# -------------------------------------------------------------------------------------
#                                                            HabitsBuilder.chart_weekday
# -------------------------------------------------------------------------------------
def test_chart_weekday_view_model():
    actual = _builder([_row(date(1999, 1, 4), 5)]).chart_weekday()

    assert isinstance(actual, WeekdayChartViewModel)
    assert len(actual.categories) == 7
    assert len(actual.drinking_day_share) == 7
    assert len(actual.intensity) == 7


def test_chart_weekday_is_one_unlabelled_layer():
    # the tab already names the year it reads, so the legend needs no span
    actual = _builder([_row(date(1999, 1, 4), 5)]).chart_weekday()

    assert [layer.label for layer in actual.layers] == [""]
    assert actual.layers[0].drinking_day_share == actual.drinking_day_share
    assert actual.layers[0].intensity == actual.intensity


def test_chart_weekday_as_dict_carries_its_layer():
    actual = _builder([_row(date(1999, 1, 4), 5)]).chart_weekday().as_dict

    assert sorted(actual) == ["categories", "heavy_threshold", "layers", "text"]
    assert len(actual["layers"]) == 1


def test_chart_weekday_categories_are_the_weekday_names_monday_first():
    actual = _builder().chart_weekday()

    assert actual.categories == [
        _("Monday"),
        _("Tuesday"),
        _("Wednesday"),
        _("Thursday"),
        _("Friday"),
        _("Saturday"),
        _("Sunday"),
    ]


def test_chart_weekday_series_are_index_aligned_with_the_categories():
    # 1999-01-04 is a Monday, so its figures belong to index 0 — the categories
    # and the series are read off the same index by the chart
    monday = date(1999, 1, 4)
    assert monday.weekday() == 0

    actual = _builder([_row(monday, 5)]).chart_weekday()

    assert actual.categories[0] == _("Monday")
    assert actual.intensity[0] == 5.0
    assert actual.intensity[1:] == [0.0] * 6


def test_chart_weekday_rate_is_a_percentage():
    # one of the three Mondays reached by 1999-01-19, so 33.3%, not 0.33
    actual = _builder([_row(date(1999, 1, 4), 5)]).chart_weekday()

    assert actual.drinking_day_share[0] == 33.3


def test_chart_weekday_rate_never_exceeds_one_hundred():
    rows = [_row(date(1999, 1, day), 5) for day in (4, 11, 18)]

    actual = _builder(rows).chart_weekday()

    assert actual.drinking_day_share[0] == 100.0


def test_chart_weekday_carries_the_heavy_day_threshold():
    # the plot line the intensity series is read against
    actual = _builder([_row(date(1999, 1, 4), 5)]).chart_weekday()

    assert actual.heavy_threshold == HEAVY_DAY_STDAV


def test_chart_weekday_names_both_units_and_neither_claims_the_others():
    actual = _builder().chart_weekday()

    assert actual.text["share_unit"] == "%"
    assert actual.text["intensity_unit"] == "Std Av"
    assert actual.text["title"] == _("Weekday profile")
    assert actual.text["share"] == _("Drinking-day rate")
    assert actual.text["intensity"] == _("Per drinking day")
    assert actual.text["threshold_label"] == _("Heavy day")


def test_chart_weekday_text_is_translated():
    # the literals, not _() against _(): that comparison holds even when the
    # msgid has no entry and the catalogue is handing back the English
    actual = _builder().chart_weekday()

    assert actual.text["title"] == "Savaitės dienų profilis"
    assert actual.text["share"] == "Vartojimo dienų dalis"
    assert actual.text["intensity"] == "Vienai vartojimo dienai"
    assert actual.categories[0] == "Pirmadienis"


def test_chart_weekday_on_no_records_is_seven_zeroed_points():
    actual = _builder().chart_weekday()

    assert actual.drinking_day_share == [0.0] * 7
    assert actual.intensity == [0.0] * 7


# -------------------------------------------------------------------------------------
#                                                                Per drinking day card
# -------------------------------------------------------------------------------------
def test_get_cards_carries_the_per_drinking_day_card():
    cards = _builder([_row(date(1999, 1, 4), 7.9)]).get_cards()

    assert [card.title for card in cards] == [_("Per drinking day")]
    assert all(isinstance(card, StatCard) for card in cards)


def test_card_per_drinking_day_above_the_heavy_threshold():
    card = _builder([_row(date(1999, 1, 4), 7.9)]).get_cards()[0]

    assert card.value == "7.9"
    assert card.unit == "Std Av"
    assert card.note == f"{_('Heavy day')}: > {HEAVY_DAY_STDAV:.0f} Std Av"
    assert card.state == "high"


def test_card_per_drinking_day_below_the_heavy_threshold():
    card = _builder([_row(date(1999, 1, 4), 4.0)]).get_cards()[0]

    assert card.value == "4.0"
    assert card.unit == "Std Av"
    assert card.state == "low"


def test_card_per_drinking_day_at_the_threshold_is_not_heavy():
    # the Heavy day rule is a strict `>`, and this card must not disagree with it
    card = _builder([_row(date(1999, 1, 4), HEAVY_DAY_STDAV)]).get_cards()[0]

    assert card.state == "low"


def test_card_per_drinking_day_explains_its_denominator_and_its_unit():
    # the note only carries the threshold, so the tooltip is where the card says
    # what the figure is divided by and why it never follows the dropdown
    card = _builder([_row(date(1999, 1, 4), 7.9)]).get_cards()[0]

    assert card.explanation == (
        _(
            "The year's Std Av divided by the days a Drink was recorded on, "
            "not by every day of the year."
        ),
        _("Always in Std Av, because the Heavy day threshold is defined there."),
    )


def test_card_per_drinking_day_empty():
    card = _builder().get_cards()[0]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")
    assert card.explanation == ()


# -------------------------------------------------------------------------------------
#                                                                       HabitsTab.build
# -------------------------------------------------------------------------------------
@time_machine.travel("1999-06-01")
def test_build_returns_the_chart_and_the_cards(main_user):
    DrinkFactory(date=date(1999, 1, 4), stdav=7.9)

    actual = HabitsTab.build(main_user, 1999)

    assert isinstance(actual["chart_weekday"], WeekdayChartViewModel)
    assert len(actual["chart_weekday"].categories) == 7
    assert [card.title for card in actual["cards"]] == [_("Per drinking day")]


@time_machine.travel("1999-06-01")
def test_build_on_a_year_with_no_drinks_does_not_raise(main_user):
    actual = HabitsTab.build(main_user, 1999)

    assert actual["chart_weekday"].intensity == [0.0] * 7
    assert actual["cards"][0].state == "empty"


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
@time_machine.travel("1999-06-01")
def test_build_is_the_same_tab_under_every_drink_type(drink_type, main_user):
    """Nothing on this tab follows the drink-type dropdown.

    The rate is a ratio and the intensity is read against ``HEAVY_DAY_STDAV``, a
    threshold defined in Std Av — so converting either would leave the plot line
    marking a level the columns no longer measure.

    This has to be asserted here rather than against ``HabitsBuilder``: the
    builder is handed a ``FrequencyStats`` and never sees a drink type at all,
    so a test that parametrizes one at that layer cannot fail. ``build`` is
    where the drink type genuinely arrives — ``ConsumptionYear`` annotates
    ``DataRow.qty`` off ``user.drink_type`` — so this is where the pin bites.
    """
    main_user.drink_type = drink_type
    DrinkFactory(date=date(1999, 1, 4), stdav=7.9)  # a Monday

    actual = HabitsTab.build(main_user, 1999)
    chart = actual["chart_weekday"]

    # 1 of the 22 Mondays reached by 1999-06-01, at 7.9 Std Av on the one
    assert chart.drinking_day_share[0] == 4.5
    assert chart.intensity[0] == 7.9
    assert chart.text["intensity_unit"] == "Std Av"
    assert chart.heavy_threshold == HEAVY_DAY_STDAV
    assert actual["cards"][0].value == "7.9"
    assert actual["cards"][0].unit == "Std Av"
