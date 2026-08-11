from datetime import date
from types import SimpleNamespace

import pytest
import time_machine
from django.urls import reverse
from django.utils.translation import gettext as _

from ....core.lib import stat_card
from ....core.lib.calendar_grid import CalendarYearViewModel
from ....core.lib.stat_card import StatCard
from ...lib.drinks_frequency import FrequencyStats
from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DataRow, DrinkStats
from ...services.index_tab import DryDaysViewModel, IndexBuilder, IndexTab
from ..factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(name="drink_converter")
def fixture_drink_converter():
    return DrinkConverter("beer")


def _row(dt: date, stdav: float, qty: float = 0.0) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=qty)


def _frequency(current=(), past=(), today=date(1999, 1, 10)) -> FrequencyStats:
    return FrequencyStats(current_daily=current, past_daily=past, today=today)


def _stats(drink_converter, total_quantity=0.0, avg=0.0, year=1999):
    stdav = total_quantity * drink_converter.stdav_per_unit
    return SimpleNamespace(
        year=year,
        yearly=SimpleNamespace(
            total_quantity=total_quantity,
            avg_daily_volume=avg,
            stdav=stdav,
            pure_alcohol_liters=drink_converter.stdav_to_alcohol(stdav),
            avg_daily_stdav=avg,
        ),
    )


def _card_builder(
    drink_converter,
    total_quantity=0.0,
    avg=0.0,
    target=0.0,
    past_quantity=0.0,
    past_avg=0.0,
    **kwargs,
):
    return IndexBuilder(
        converter=drink_converter,
        drink_stats=_stats(drink_converter, total_quantity, avg),
        previous_stats=_stats(drink_converter, past_quantity, past_avg, year=1998),
        target=target,
        **kwargs,
    )


@pytest.mark.parametrize(
    "past, current, expect",
    [
        (date(1998, 1, 1), None, DryDaysViewModel(date(1998, 1, 1), 367)),
        (None, date(1999, 1, 1), DryDaysViewModel(date(1999, 1, 1), 2)),
        (date(1998, 1, 1), date(1999, 1, 1), DryDaysViewModel(date(1999, 1, 1), 2)),
        (None, None, DryDaysViewModel(None, 0)),
    ],
)
@time_machine.travel("1999-01-03")
def test_dry_days(past, current, expect, main_user, drink_converter):
    DrinkFactory()

    actual = IndexBuilder(
        converter=drink_converter,
        drink_stats=DrinkStats(drink_converter),
        latest_past_date=past,
        latest_current_date=current,
    ).tbl_dry_days()

    assert actual == expect


@time_machine.travel("2019-10-10")
def test_std_av(main_user, drink_converter):
    actual = IndexBuilder(
        converter=drink_converter, drink_stats=DrinkStats(drink_converter)
    )._build_conversion_rows(2019, 273.5)

    assert len(actual) == 4

    assert actual[0].title == "Alus, 0.5L"
    assert round(actual[0].total, 2) == 273.5
    assert round(actual[0].per_day, 2) == 0.97
    assert round(actual[0].per_week, 2) == 6.67
    assert round(actual[0].per_month, 2) == 27.35

    assert actual[1].title == "Vynas, 0.75L"
    assert round(actual[1].total, 2) == 85.47
    assert round(actual[1].per_day, 2) == 0.3
    assert round(actual[1].per_week, 2) == 2.08
    assert round(actual[1].per_month, 2) == 8.55

    assert actual[2].title == "Degtinė, 1L"
    assert round(actual[2].total, 2) == 17.09
    assert round(actual[2].per_day, 2) == 0.06
    assert round(actual[2].per_week, 2) == 0.42
    assert round(actual[2].per_month, 2) == 1.71

    assert actual[3].title == "Std Av"
    assert round(actual[3].total, 2) == 683.75
    assert round(actual[3].per_day, 2) == 2.42
    assert round(actual[3].per_week, 2) == 16.68
    assert round(actual[3].per_month, 2) == 68.38


@time_machine.travel("2019-10-10")
def test_std_av_past_recods(main_user, drink_converter):
    actual = IndexBuilder(
        converter=drink_converter, drink_stats=DrinkStats(drink_converter)
    )._build_conversion_rows(1999, 273.5)

    assert len(actual) == 4

    assert actual[0].title == "Alus, 0.5L"
    assert round(actual[0].total, 2) == 273.5
    assert round(actual[0].per_day, 2) == 0.75
    assert round(actual[0].per_week, 2) == 5.26
    assert round(actual[0].per_month, 2) == 22.79

    assert actual[1].title == "Vynas, 0.75L"
    assert round(actual[1].total, 2) == 85.47
    assert round(actual[1].per_day, 2) == 0.23
    assert round(actual[1].per_week, 2) == 1.64
    assert round(actual[1].per_month, 2) == 7.12

    assert actual[2].title == "Degtinė, 1L"
    assert round(actual[2].total, 2) == 17.09
    assert round(actual[2].per_day, 2) == 0.05
    assert round(actual[2].per_week, 2) == 0.33
    assert round(actual[2].per_month, 2) == 1.42

    assert actual[3].title == "Std Av"
    assert round(actual[3].total, 2) == 683.75
    assert round(actual[3].per_day, 2) == 1.87
    assert round(actual[3].per_week, 2) == 13.15
    assert round(actual[3].per_month, 2) == 56.98


def test_dry_days_view_model_has_data():
    model_with_data = DryDaysViewModel(date=date(2026, 5, 8), delta=10)
    assert model_with_data.has_data is True

    empty_model = DryDaysViewModel()
    assert empty_model.has_data is False


# -------------------------------------------------------------------------------------
#                                                          IndexBuilder.get_cards
# -------------------------------------------------------------------------------------
def test_get_cards_order(main_user, drink_converter):
    # six, the Daily limit last. A seventh should have to argue with this test
    cards = _card_builder(drink_converter, total_quantity=100.0, avg=300.0).get_cards()

    assert [c.title for c in cards] == [
        _("Days dry"),
        _("Drinking days"),
        _("Std drinks"),
        _("Avg per day"),
        _("Pure alcohol"),
        _("Daily limit"),
    ]
    assert all(isinstance(c, StatCard) for c in cards)


# -------------------------------------------------------------------------------------
#                                                    IndexBuilder.get_cards: Daily limit
# -------------------------------------------------------------------------------------
def test_card_limit_with_target(main_user, drink_converter):
    card = _card_builder(
        drink_converter, target=500.0, target_id=7, pcs_per_day=0.6
    ).get_cards()[5]

    assert card.title == _("Daily limit")
    assert card.value == "500"
    assert card.unit == _("ml")
    assert card.note == f"0.6 {_('pcs')} / {_('day')}"
    assert card.edit_url == reverse("drinks:target_update", kwargs={"pk": 7})


def test_card_limit_without_target(main_user, drink_converter):
    """An unset limit is an em dash and a note, and its pencil opens a new goal."""
    card = _card_builder(drink_converter).get_cards()[5]

    assert card.title == _("Daily limit")
    assert card.value == ""
    assert card.unit == ""
    assert card.note == _("No limit set")
    assert card.state == stat_card.EMPTY
    assert card.edit_url == reverse("drinks:target_new", kwargs={"tab": "index"})


def test_card_limit_in_stdav_carries_no_unit(main_user):
    """Std Av is read as typed, so the figure carries no unit beside it — and it
    keeps the decimal a whole number would destroy."""
    card = _card_builder(
        DrinkConverter("stdav"), target=1.5, target_id=7, pcs_per_day=1.5
    ).get_cards()[5]

    assert card.value == "1.5"
    assert card.unit == ""


@time_machine.travel("1999-01-05")
def test_card_dry_days_with_data(main_user, drink_converter):
    card = _card_builder(
        drink_converter, latest_current_date=date(1999, 1, 1)
    ).get_cards()[0]

    assert card.state == "neutral"
    assert card.value == "4"
    assert card.note == "1999-01-01"


def test_card_dry_days_empty(main_user, drink_converter):
    card = _card_builder(drink_converter).get_cards()[0]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")


def test_card_std_drinks_with_data(main_user, drink_converter):
    card = _card_builder(drink_converter, total_quantity=100.0).get_cards()[2]

    assert card.state == "neutral"
    assert card.value == "250"  # 100 units * 2.5 std av per beer
    assert card.note == _("Std Av this year")


def test_card_std_drinks_notes_last_year(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=100.0, past_quantity=80.0
    ).get_cards()[2]

    assert card.value == "250"
    assert card.note == f"{_('Last year')} 200"
    assert card.state == "worsening"
    assert card.show_icon is True
    assert card.improving is False


def test_card_std_drinks_less_than_last_year_is_improving(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=80.0, past_quantity=100.0
    ).get_cards()[2]

    assert card.note == f"{_('Last year')} 250"
    assert card.state == "improving"
    assert card.improving is True


def test_card_std_drinks_empty(main_user, drink_converter):
    card = _card_builder(drink_converter, total_quantity=0.0).get_cards()[2]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")


def test_card_avg_per_day_over_limit(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=100.0, avg=300.0, target=250.0
    ).get_cards()[3]

    assert card.state == "high"
    assert card.value == "300"
    assert card.unit == "ml"
    assert card.note == f"50 {_('over the limit')}"
    assert card.explanation == f"ml {_('per calendar day')}"


def test_card_avg_per_day_under_limit(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=100.0, avg=300.0, target=400.0
    ).get_cards()[3]

    assert card.state == "low"
    assert card.value == "300"
    assert card.unit == "ml"
    assert card.note == f"100 {_('under the limit')}"
    assert card.explanation == f"ml {_('per calendar day')}"


def test_card_avg_per_day_equal_limit_is_positive(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=100.0, avg=250.0, target=250.0
    ).get_cards()[3]

    assert card.state == "low"
    assert card.note == f"0 {_('under the limit')}"
    assert card.explanation == f"ml {_('per calendar day')}"


def test_card_avg_per_day_no_limit(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=100.0, avg=300.0, target=0.0
    ).get_cards()[3]

    assert card.state == "neutral"
    assert card.value == "300"
    assert card.unit == "ml"
    assert card.note == _("No limit set")
    assert card.explanation == f"ml {_('per calendar day')}"


def test_card_avg_per_day_stdav_over_limit(main_user):
    converter = DrinkConverter("stdav")
    card = _card_builder(
        converter, total_quantity=100.0, avg=3.0, target=2.5
    ).get_cards()[3]

    assert card.state == "high"
    assert card.value == "3.0"
    # Std Av is shown as typed: the explanation names the unit, the figure does not
    assert card.unit == ""
    assert card.note == f"0.5 {_('over the limit')}"
    assert card.explanation == f"Std Av {_('per calendar day')}"


def test_card_avg_per_day_stdav_under_limit(main_user):
    converter = DrinkConverter("stdav")
    card = _card_builder(
        converter, total_quantity=100.0, avg=2.0, target=2.5
    ).get_cards()[3]

    assert card.state == "low"
    assert card.value == "2.0"
    assert card.note == f"0.5 {_('under the limit')}"
    assert card.explanation == f"Std Av {_('per calendar day')}"


def test_card_avg_per_day_notes_last_year_but_is_still_coloured_by_the_limit(
    main_user, drink_converter
):
    """The Drink Target is a real threshold, so it keeps the colour; the baseline
    only points the arrow."""
    card = _card_builder(
        drink_converter,
        total_quantity=100.0,
        avg=300.0,
        target=400.0,
        past_quantity=80.0,
        past_avg=280.0,
    ).get_cards()[3]

    assert card.state == "low"
    assert card.note == f"{_('Last year')} 280"
    assert card.show_icon is True
    assert card.improving is False
    assert card.explanation == (
        f"ml {_('per calendar day')} · 100 {_('under the limit')}"
    )


def test_card_avg_per_day_without_a_limit_compares_with_last_year(
    main_user, drink_converter
):
    card = _card_builder(
        drink_converter,
        total_quantity=100.0,
        avg=300.0,
        target=0.0,
        past_quantity=80.0,
        past_avg=320.0,
    ).get_cards()[3]

    assert card.state == "improving"
    assert card.note == f"{_('Last year')} 320"
    assert card.explanation == f"ml {_('per calendar day')}"


def test_card_avg_per_day_stdav_reads_the_baseline_in_std_av_too(main_user):
    """The figure switches measure for `stdav`; a baseline left on
    `avg_daily_volume` would state last year in millilitres beside it."""
    converter = DrinkConverter("stdav")
    card = _card_builder(
        converter,
        total_quantity=100.0,
        avg=3.0,
        target=2.5,
        past_quantity=80.0,
        past_avg=2.0,
    ).get_cards()[3]

    assert card.value == "3.0"
    assert card.note == f"{_('Last year')} 2.0"


def test_card_avg_per_day_empty(main_user, drink_converter):
    card = _card_builder(drink_converter, total_quantity=0.0, avg=0.0).get_cards()[3]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")


def test_card_pure_alcohol_with_data(main_user, drink_converter):
    card = _card_builder(drink_converter, total_quantity=100.0).get_cards()[4]

    assert card.state == "neutral"
    assert card.value == "2.5"  # 100 units -> 250 std av -> 2.5 L pure alcohol
    assert card.unit == "L"
    assert card.note == _("this year")


def test_card_pure_alcohol_notes_last_year(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=100.0, past_quantity=80.0
    ).get_cards()[4]

    assert card.value == "2.5"
    assert card.unit == "L"
    assert card.note == f"{_('Last year')} 2.0"
    assert card.state == "worsening"
    assert card.show_icon is True


def test_card_pure_alcohol_empty(main_user, drink_converter):
    card = _card_builder(drink_converter, total_quantity=0.0).get_cards()[4]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")


# -------------------------------------------------------------------------------------
#                                                                    Drinking days card
# -------------------------------------------------------------------------------------
def test_card_drinking_days_with_data(main_user, drink_converter):
    # 4 drinking days out of the 10 elapsed, against 2 last year
    current = [_row(date(1999, 1, i), 3) for i in range(1, 5)]
    past = [_row(date(1998, 1, 1), 3), _row(date(1998, 1, 2), 3)]

    card = _card_builder(
        drink_converter,
        total_quantity=100.0,
        frequency_stats=_frequency(current, past),
    ).get_cards()[1]

    assert card.value == "4"
    assert card.note == f"{_('Last year')} 2"
    assert card.state == "worsening"
    assert card.show_icon is True


def test_card_drinking_days_keeps_the_share_in_its_explanation(
    main_user, drink_converter
):
    current = [_row(date(1999, 1, i), 3) for i in range(1, 5)]
    past = [_row(date(1998, 1, 1), 3)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current, past)
    ).get_cards()[1]

    assert card.explanation.startswith(
        _("%(share)s%% of the year so far") % {"share": "40"}
    )


def test_card_drinking_days_note_on_a_year_already_over(main_user, drink_converter):
    # the year is finished, so the share is of all 365 days and nothing is "so far"
    current = [_row(date(1999, 1, i), 3) for i in range(1, 5)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current, today=date(2000, 6, 1))
    ).get_cards()[1]

    assert card.explanation.startswith(_("%(share)s%% of the year") % {"share": "1"})


def test_card_drinking_days_fewer_than_last_year_is_improving(
    main_user, drink_converter
):
    current = [_row(date(1999, 1, 1), 3)]
    past = [_row(date(1998, 1, 1), 3), _row(date(1998, 1, 2), 3)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current, past)
    ).get_cards()[1]

    assert card.state == "improving"


def test_card_drinking_days_without_a_prior_year(main_user, drink_converter):
    current = [_row(date(1999, 1, i), 3) for i in range(1, 5)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current)
    ).get_cards()[1]

    assert card.value == "4"
    assert card.state == "neutral"
    assert card.show_icon is False
    # with no baseline the card falls back to the note it always had
    assert card.note == _("%(share)s%% of the year so far") % {"share": "40"}


def test_card_drinking_days_empty(main_user, drink_converter):
    card = _card_builder(drink_converter, frequency_stats=_frequency()).get_cards()[1]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")


# -------------------------------------------------------------------------------------
#                                                                         IndexTab.build
# -------------------------------------------------------------------------------------
@time_machine.travel("1999-06-01")
def test_index_tab_build_returns_expected_keys(main_user):
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)

    actual = IndexTab.build(main_user, 1999)

    assert set(actual) == {
        "all_years",
        "chart_quantity",
        "chart_consumption",
        "tbl_std_av",
        "cards",
        "calendar",
    }
    assert len(actual["cards"]) == 6
    assert all(isinstance(c, StatCard) for c in actual["cards"])
    assert isinstance(actual["calendar"], CalendarYearViewModel)


@time_machine.travel("1999-06-01")
def test_index_tab_build_charts_stop_at_the_year_boundary(main_user):
    # a month the year has not reached is not a month with no Drinks in it
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)

    actual = IndexTab.build(main_user, 1999)

    assert actual["chart_consumption"].data[6:] == [None] * 6
    assert actual["chart_quantity"].data[6:] == [None] * 6


@time_machine.travel("1999-12-31")
def test_index_tab_build_charts_run_to_december_once_the_year_is_over(main_user):
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)

    actual = IndexTab.build(main_user, 1999)

    assert None not in actual["chart_consumption"].data
    assert None not in actual["chart_quantity"].data


@time_machine.travel("1999-06-01")
def test_index_tab_build_frequency_cards_read_the_daily_rows(main_user):
    # two Drinks on one day and one on another: two Drinking days, not three
    # rows — the count DrinkStats' monthly rows could not have produced
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1999, 2, 20), stdav=5.0)
    DrinkFactory(date=date(1998, 1, 10), stdav=2.5)

    cards = IndexTab.build(main_user, 1999)["cards"]

    assert cards[1].value == "2"
    assert cards[1].state == "worsening"  # 2 days against last year's 1


@time_machine.travel("1999-06-01")
def test_index_tab_build_limit_has_data(main_user):
    target = DrinkTargetFactory(user=main_user, year=1999, quantity=100)

    card = IndexTab.build(main_user, 1999)["cards"][5]

    assert card.title == _("Daily limit")
    assert card.state == stat_card.NEUTRAL
    assert card.value == "100"
    assert card.unit == "ml"
    assert card.note.endswith(f"{_('pcs')} / {_('day')}")
    assert card.edit_url == reverse("drinks:target_update", kwargs={"pk": target.pk})


@time_machine.travel("1999-06-01")
def test_index_tab_build_limit_stdav(main_user):
    main_user.drink_type = "stdav"
    DrinkTargetFactory(user=main_user, year=1999, quantity=2.5, drink_type="stdav")

    card = IndexTab.build(main_user, 1999)["cards"][5]

    # Std Av is read as typed: the figure keeps its decimal and carries no unit
    assert card.value == "2.5"
    assert card.unit == ""


@time_machine.travel("1999-06-01")
def test_index_tab_build_limit_no_target(main_user):
    card = IndexTab.build(main_user, 1999)["cards"][5]

    assert card.title == _("Daily limit")
    assert card.state == stat_card.EMPTY
    assert card.value == ""
    assert card.note == _("No limit set")
    assert card.edit_url == reverse("drinks:target_new", kwargs={"tab": "index"})


@time_machine.travel("1999-06-01")
def test_index_tab_build_reads_last_year_without_a_further_query(
    main_user, django_assert_num_queries
):
    """The baseline rides on the daily rows FrequencyStats already pulls; reaching
    for `records.previous.monthly` instead would cost a query per page."""
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1998, 1, 10), stdav=2.5)

    with django_assert_num_queries(6):
        IndexTab.build(main_user, 1999)


@time_machine.travel("1999-06-01")
def test_index_tab_build_states_last_year_only_as_far_as_today(main_user):
    """A Drink last November is past this June, so it is no part of the baseline
    the cards state — the Year boundary cuts it off."""
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1998, 1, 10), stdav=10.0)
    DrinkFactory(date=date(1998, 11, 20), stdav=100.0)

    cards = {card.title: card for card in IndexTab.build(main_user, 1999)["cards"]}

    assert cards[_("Std drinks")].note == f"{_('Last year')} 10"
