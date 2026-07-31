from datetime import date
from types import SimpleNamespace

import pytest
import time_machine
from django.utils.translation import gettext as _

from project.drinks.lib.drinks_stats import DrinkStats

from ....core.lib.calendar_grid import CalendarYearViewModel
from ...lib.drinks_frequency import FrequencyStats
from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_risk import HEAVY_DAY_STDAV
from ...lib.drinks_stats import DataRow
from ...services.index_tab import (
    DryDaysViewModel,
    IndexBuilder,
    IndexTab,
    LimitCardViewModel,
)
from ...services.stat_card import StatCard
from ..factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(name="drink_converter")
def fixture_drink_converter():
    return DrinkConverter("beer")


def _row(dt: date, stdav: float, qty: float = 0.0) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=qty)


def _frequency(current=(), past=(), today=date(1999, 1, 10)) -> FrequencyStats:
    return FrequencyStats(current_daily=current, past_daily=past, today=today)


def _card_builder(drink_converter, total_quantity=0.0, avg=0.0, target=0.0, **kwargs):
    stdav = total_quantity * drink_converter.stdav_per_unit
    pure_alcohol = drink_converter.stdav_to_alcohol(stdav)
    stats = SimpleNamespace(
        year=1999,
        yearly=SimpleNamespace(
            total_quantity=total_quantity,
            avg_daily_volume=avg,
            stdav=stdav,
            pure_alcohol_liters=pure_alcohol,
            avg_daily_stdav=avg,
        ),
    )
    return IndexBuilder(
        converter=drink_converter, drink_stats=stats, target=target, **kwargs
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


def test_dry_days_no_records(main_user, drink_converter):
    actual = IndexBuilder(
        converter=drink_converter, drink_stats=DrinkStats(drink_converter)
    ).tbl_dry_days()

    assert actual == DryDaysViewModel(date=None, delta=0)


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


@pytest.mark.parametrize(
    "drink_type, qty, expect",
    [
        ("beer", 4, 0.1),
        ("wine", 1.25, 0.1),
        ("vodka", 0.25, 0.1),
        ("stdav", 10, 0.1),
    ],
)
def test_tbl_alcohol(drink_type, qty, expect, main_user, drink_converter):
    main_user.drink_type = drink_type

    stats = SimpleNamespace(
        year=1999,
        yearly=SimpleNamespace(
            total_quantity=qty,
            avg_daily_volume=0.0,
        ),
    )

    actual = IndexBuilder(
        converter=DrinkConverter(drink_type), drink_stats=stats
    ).tbl_alcohol()

    assert actual.liters == expect


def test_dry_days_view_model_has_data():
    model_with_data = DryDaysViewModel(date=date(2026, 5, 8), delta=10)
    assert model_with_data.has_data is True

    empty_model = DryDaysViewModel()
    assert empty_model.has_data is False


# -------------------------------------------------------------------------------------
#                                                          IndexBuilder.get_cards
# -------------------------------------------------------------------------------------
def test_get_cards_returns_six(main_user, drink_converter):
    cards = _card_builder(drink_converter, total_quantity=100.0, avg=300.0).get_cards()

    assert len(cards) == 6
    assert all(isinstance(c, StatCard) for c in cards)


def test_get_cards_order(main_user, drink_converter):
    cards = _card_builder(drink_converter, total_quantity=100.0, avg=300.0).get_cards()

    assert [c.title for c in cards] == [
        _("Days dry"),
        _("Drinking days"),
        _("Std drinks"),
        _("Avg per day"),
        _("Per drinking day"),
        _("Pure alcohol"),
    ]


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
    assert card.value == "300 ml"
    assert card.note == f"50 {_('over the limit')} · ml {_('per calendar day')}"


def test_card_avg_per_day_under_limit(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=100.0, avg=300.0, target=400.0
    ).get_cards()[3]

    assert card.state == "low"
    assert card.value == "300 ml"
    assert card.note == f"100 {_('under the limit')} · ml {_('per calendar day')}"


def test_card_avg_per_day_equal_limit_is_positive(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=100.0, avg=250.0, target=250.0
    ).get_cards()[3]

    assert card.state == "low"
    assert card.note == f"0 {_('under the limit')} · ml {_('per calendar day')}"


def test_card_avg_per_day_no_limit(main_user, drink_converter):
    card = _card_builder(
        drink_converter, total_quantity=100.0, avg=300.0, target=0.0
    ).get_cards()[3]

    assert card.state == "neutral"
    assert card.value == "300 ml"
    assert card.note == f"{_('No limit set')} · ml {_('per calendar day')}"


def test_card_avg_per_day_stdav_over_limit(main_user):
    converter = DrinkConverter("stdav")
    card = _card_builder(
        converter, total_quantity=100.0, avg=3.0, target=2.5
    ).get_cards()[3]

    assert card.state == "high"
    assert card.value == "3.0"
    assert card.note == f"0.5 {_('over the limit')} · Std Av {_('per calendar day')}"


def test_card_avg_per_day_stdav_under_limit(main_user):
    converter = DrinkConverter("stdav")
    card = _card_builder(
        converter, total_quantity=100.0, avg=2.0, target=2.5
    ).get_cards()[3]

    assert card.state == "low"
    assert card.value == "2.0"
    assert card.note == f"0.5 {_('under the limit')} · Std Av {_('per calendar day')}"


def test_card_avg_per_day_names_its_denominator_and_unit(main_user, drink_converter):
    # the Std Av card next to it is per drinking day, so this note has to say
    # which days its own average is spread over, and in which unit
    card = _card_builder(
        drink_converter, total_quantity=100.0, avg=300.0, target=250.0
    ).get_cards()[3]

    assert _("per calendar day") in card.note
    assert "ml" in card.note


def test_card_avg_per_day_empty(main_user, drink_converter):
    card = _card_builder(drink_converter, total_quantity=0.0, avg=0.0).get_cards()[3]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")


def test_card_pure_alcohol_with_data(main_user, drink_converter):
    card = _card_builder(drink_converter, total_quantity=100.0).get_cards()[5]

    assert card.state == "neutral"
    assert card.value == "2.5 L"  # 100 units -> 250 std av -> 2.5 L pure alcohol
    assert card.note == _("this year")


def test_card_pure_alcohol_empty(main_user, drink_converter):
    card = _card_builder(drink_converter, total_quantity=0.0).get_cards()[5]

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
    assert card.note == _("%(share)s%% of the year so far") % {"share": "40"}
    assert card.state == "worsening"
    assert card.show_icon is True


def test_card_drinking_days_note_counts_the_days_elapsed_while_the_year_runs(
    main_user, drink_converter
):
    # 4 of the 10 days elapsed, not 4 of 365 — so the note says which
    current = [_row(date(1999, 1, i), 3) for i in range(1, 5)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current, today=date(1999, 1, 10))
    ).get_cards()[1]

    assert card.note == _("%(share)s%% of the year so far") % {"share": "40"}


def test_card_drinking_days_note_on_a_year_already_over(main_user, drink_converter):
    # the year is finished, so the share is of all 365 days and nothing is "so far"
    current = [_row(date(1999, 1, i), 3) for i in range(1, 5)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current, today=date(2000, 6, 1))
    ).get_cards()[1]

    assert card.note == _("%(share)s%% of the year") % {"share": "1"}


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


def test_card_drinking_days_empty(main_user, drink_converter):
    card = _card_builder(drink_converter, frequency_stats=_frequency()).get_cards()[1]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")


# -------------------------------------------------------------------------------------
#                                                                Per drinking day card
# -------------------------------------------------------------------------------------
def test_card_per_drinking_day_above_the_heavy_threshold(main_user, drink_converter):
    current = [_row(date(1999, 1, 1), 7.9)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current)
    ).get_cards()[4]

    assert card.value == "7.9 Std Av"
    assert card.note == f"{_('Heavy day')}: > {HEAVY_DAY_STDAV:.0f} Std Av"
    assert card.state == "high"


def test_card_per_drinking_day_below_the_heavy_threshold(main_user, drink_converter):
    current = [_row(date(1999, 1, 1), 4.0)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current)
    ).get_cards()[4]

    assert card.value == "4.0 Std Av"
    assert card.state == "low"


def test_card_per_drinking_day_at_the_threshold_is_not_heavy(
    main_user, drink_converter
):
    # the Heavy day rule is a strict `>`, and this card must not disagree with it
    current = [_row(date(1999, 1, 1), HEAVY_DAY_STDAV)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current)
    ).get_cards()[4]

    assert card.state == "low"


def test_card_per_drinking_day_explains_its_denominator_and_its_unit(
    main_user, drink_converter
):
    # the note only carries the threshold, so the tooltip is where the card says
    # what the figure is divided by and why it never follows the dropdown
    current = [_row(date(1999, 1, 1), 7.9)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current)
    ).get_cards()[4]

    assert card.explanation == "{} {}".format(
        _(
            "The year's Std Av divided by the days a Drink was recorded on, "
            "not by every day of the year."
        ),
        _("Always in Std Av, because the Heavy day threshold is defined there."),
    )


def test_card_per_drinking_day_empty(main_user, drink_converter):
    card = _card_builder(drink_converter, frequency_stats=_frequency()).get_cards()[4]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")
    assert card.explanation == ""


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
def test_card_per_drinking_day_is_std_av_under_every_drink_type(drink_type, main_user):
    converter = DrinkConverter(drink_type)
    current = [_row(date(1999, 1, 1), 7.9, qty=7.9 * converter.ratio)]

    card = _card_builder(converter, frequency_stats=_frequency(current)).get_cards()[4]

    assert card.value == "7.9 Std Av"


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
        "limit",
        "calendar",
    }
    assert len(actual["cards"]) == 6
    assert all(isinstance(c, StatCard) for c in actual["cards"])
    assert isinstance(actual["limit"], LimitCardViewModel)
    assert isinstance(actual["calendar"], CalendarYearViewModel)


@time_machine.travel("1999-06-01")
def test_index_tab_build_frequency_cards_read_the_daily_rows(main_user):
    # two Drinks on one day and one on another: two Drinking days, 10 Std Av
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1999, 2, 20), stdav=5.0)
    DrinkFactory(date=date(1998, 1, 10), stdav=2.5)

    cards = IndexTab.build(main_user, 1999)["cards"]

    assert cards[1].value == "2"  # Drinking days, not three rows
    assert cards[4].value == "5.0 Std Av"  # 10 Std Av over 2 drinking days
    assert cards[1].state == "worsening"  # 2 days against last year's 1


@time_machine.travel("1999-06-01")
def test_index_tab_build_limit_has_data(main_user):
    DrinkTargetFactory(user=main_user, year=1999, quantity=100)

    limit = IndexTab.build(main_user, 1999)["limit"]

    assert limit.has_data is True
    assert limit.unit == "ml"
    assert limit.ml > 0.0
    assert limit.pcs > 0.0
    assert limit.target_id > 0


@time_machine.travel("1999-06-01")
def test_index_tab_build_limit_stdav(main_user):
    main_user.drink_type = "stdav"
    DrinkTargetFactory(user=main_user, year=1999, quantity=2.5, drink_type="stdav")

    limit = IndexTab.build(main_user, 1999)["limit"]

    assert limit.has_data is True
    assert limit.unit == "Std Av"
    assert limit.ml == 2.5
    assert limit.pcs == 2.5


@time_machine.travel("1999-06-01")
def test_index_tab_build_limit_no_target(main_user):
    limit = IndexTab.build(main_user, 1999)["limit"]

    assert limit.has_data is False
    assert limit.ml == 0.0
    assert limit.pcs == 0.0
    assert limit.target_id == 0
