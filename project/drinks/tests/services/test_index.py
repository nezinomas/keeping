from datetime import date
from types import SimpleNamespace

import pytest
from django.urls import reverse
from django.utils.translation import gettext as _

from ....core.lib import stat_card
from ....core.lib.day_stats import NoPastRecord, PastRecord
from ...lib.drinks_frequency import FrequencyStats
from ...lib.drinks_options import DrinkConverter, stdav_to_alcohol
from ...lib.drinks_stats import DataRow
from ...services.index_tab import (
    DailyLimit,
    DryDaysViewModel,
    IndexBuilder,
    IndexTab,
    NoDailyLimit,
    NoDryDaysViewModel,
)
from ..factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(name="drink_converter")
def fixture_drink_converter():
    return DrinkConverter("beer")


def _row(dt: date, stdav: float, qty: float = 0.0) -> DataRow:
    return DataRow(date=dt, stdav=stdav, qty=qty)


def _frequency(
    current=(), past=(), today=date(1999, 1, 10), year=1999
) -> FrequencyStats:
    return FrequencyStats(
        current_daily=current, past_daily=past, year=year, today=today
    )


def _stats(drink_converter, total_quantity=0.0, avg=0.0, year=1999):
    stdav = drink_converter.servings_to_stdav(total_quantity)
    volume, std = avg, 0.0
    if drink_converter.is_canonical:
        volume, std = 0.0, avg
    return SimpleNamespace(
        year=year,
        yearly=SimpleNamespace(
            total_quantity=total_quantity,
            avg_daily_volume=volume,
            stdav=stdav,
            pure_alcohol_liters=stdav_to_alcohol(stdav),
            avg_daily_stdav=std,
        ),
    )


def _card_builder(
    drink_converter,
    total_quantity=0.0,
    avg=0.0,
    target=0.0,
    past_quantity=0.0,
    past_avg=0.0,
    year=1999,
    **kwargs,
):
    kwargs.setdefault("today", date(1999, 6, 1))
    kwargs.setdefault("frequency_stats", _frequency())

    return IndexBuilder(
        converter=drink_converter,
        drink_stats=_stats(drink_converter, total_quantity, avg, year=year),
        previous_stats=_stats(drink_converter, past_quantity, past_avg, year=year - 1),
        limit=DailyLimit(target) if target else NoDailyLimit(),
        **kwargs,
    )


@pytest.mark.parametrize(
    "latest, expect",
    [
        (PastRecord(date(1998, 1, 1)), DryDaysViewModel(date(1998, 1, 1), 367)),
        (PastRecord(date(1999, 1, 1)), DryDaysViewModel(date(1999, 1, 1), 2)),
        (NoPastRecord(), NoDryDaysViewModel()),
    ],
)
def test_dry_days(latest, expect, main_user, drink_converter):
    actual = _card_builder(
        drink_converter, latest=latest, today=date(1999, 1, 3)
    ).tbl_dry_days()

    assert actual == expect


@pytest.mark.parametrize(
    "year, expect",
    [
        pytest.param(
            2019,
            [
                ("Alus, 0.5L", 273.5, 0.97, 6.67, 27.35, False),
                ("Vynas, 0.75L", 85.47, 0.3, 2.08, 8.55, False),
                ("Degtinė, 1L", 17.09, 0.06, 0.42, 1.71, False),
                ("Std Av", 683.75, 2.42, 16.68, 68.38, True),
            ],
            id="std_av",
        ),
        pytest.param(
            1999,
            [
                ("Alus, 0.5L", 273.5, 0.75, 5.26, 22.79, False),
                ("Vynas, 0.75L", 85.47, 0.23, 1.64, 7.12, False),
                ("Degtinė, 1L", 17.09, 0.05, 0.33, 1.42, False),
                ("Std Av", 683.75, 1.87, 13.15, 56.98, True),
            ],
            id="std_av_past_recods",
        ),
    ],
)
def test_tbl_std_av_reads_the_year_in_every_drink_type(drink_converter, year, expect):
    builder = _card_builder(
        drink_converter, total_quantity=273.5, year=year, today=date(2019, 10, 10)
    )

    actual = [
        (
            row.title,
            round(row.total, 2),
            round(row.per_day, 2),
            round(row.per_week, 2),
            round(row.per_month, 2),
            row.is_total,
        )
        for row in builder.tbl_std_av().items
    ]

    assert actual == expect


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


@pytest.mark.parametrize(
    "drink_type, target, value, unit, amount",
    [
        pytest.param("beer", 500.0, "500", _("ml"), "182,5 L", id="volume"),
        # Std Av is read as typed, so the figure carries no unit beside it and
        # keeps the decimal a whole number would destroy
        pytest.param("stdav", 1.5, "1.5", "", "547,5 Std Av", id="stdav"),
    ],
)
def test_card_limit_with_target(main_user, drink_type, target, value, unit, amount):
    card = _card_builder(
        DrinkConverter(drink_type), target=target, target_id=7
    ).get_cards()[5]

    assert card.title == _("Daily limit")
    assert card.value == value
    assert card.unit == unit
    # a daily limit over 1999, read in the unit a year's total takes
    assert card.note == _("%(amount)s per year") % {"amount": amount}
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


@pytest.mark.parametrize(
    "latest, value, note",
    [
        pytest.param(PastRecord(date(1999, 1, 1)), "4", "1999-01-01", id="this_year"),
        pytest.param(PastRecord(date(1998, 12, 20)), "16", "1998-12-20", id="before"),
    ],
)
def test_card_dry_days_with_data(latest, value, note, main_user, drink_converter):
    card = _card_builder(
        drink_converter, latest=latest, today=date(1999, 1, 5)
    ).get_cards()[0]

    assert card.state == "neutral"
    assert card.value == value
    assert card.note == note


@pytest.mark.parametrize(
    "quantity, past, value, note, state, show_icon, improving",
    [
        pytest.param(
            100.0,
            0.0,
            "250",
            _("Std Av this year"),
            "neutral",
            False,
            False,
            id="alone",
        ),
        pytest.param(
            100.0,
            80.0,
            "250",
            f"{_('Last year')} 200",
            "worsening",
            True,
            False,
            id="more_than_last_year",
        ),
        pytest.param(
            80.0,
            100.0,
            "200",
            f"{_('Last year')} 250",
            "improving",
            True,
            True,
            id="less_than_last_year",
        ),
    ],
)
def test_card_std_drinks_reads_the_year_total(
    main_user, drink_converter, quantity, past, value, note, state, show_icon, improving
):
    # 2.5 std av per beer
    card = _card_builder(
        drink_converter, total_quantity=quantity, past_quantity=past
    ).get_cards()[2]

    assert card.value == value
    assert card.note == note
    assert card.state == state
    assert card.show_icon is show_icon
    assert card.improving is improving


@pytest.mark.parametrize(
    "drink_type, avg, target, state, value, unit, note, explained_in",
    [
        pytest.param(
            "beer", 300.0, 250.0, "high", "300", "ml", "50 {over}", "ml", id="over"
        ),
        pytest.param(
            "beer", 300.0, 400.0, "low", "300", "ml", "100 {under}", "ml", id="under"
        ),
        pytest.param(
            "beer", 250.0, 250.0, "low", "250", "ml", "0 {under}", "ml", id="equal"
        ),
        pytest.param(
            "beer", 300.0, 0.0, "neutral", "300", "ml", "{none}", "ml", id="no_limit"
        ),
        pytest.param(
            "stdav",
            3.0,
            2.5,
            "high",
            "3.0",
            "",
            "0.5 {over}",
            "Std Av",
            id="stdav_over",
        ),
        pytest.param(
            "stdav",
            2.0,
            2.5,
            "low",
            "2.0",
            "",
            "0.5 {under}",
            "Std Av",
            id="stdav_under",
        ),
    ],
)
def test_card_avg_per_day_reads_against_the_limit(
    main_user, drink_type, avg, target, state, value, unit, note, explained_in
):
    """Std Av is shown as typed: the explanation names the unit, the figure does not."""
    card = _card_builder(
        DrinkConverter(drink_type), total_quantity=100.0, avg=avg, target=target
    ).get_cards()[3]

    assert card.state == state
    assert card.value == value
    assert card.unit == unit
    assert card.note == note.format(
        over=_("over the limit"), under=_("under the limit"), none=_("No limit set")
    )
    assert card.explanation == (f"{explained_in} {_('per calendar day')}",)
    # no last year, so no arrow
    assert card.show_icon is False


@pytest.mark.parametrize(
    "past_avg, improving",
    [
        pytest.param(280.0, False, id="more_than_last_year"),
        pytest.param(320.0, True, id="less_than_last_year"),
    ],
)
def test_card_avg_per_day_notes_last_year_but_is_still_coloured_by_the_limit(
    main_user, drink_converter, past_avg, improving
):
    """The Drink Target is a real threshold, so it keeps the colour; the baseline
    only points the arrow."""
    card = _card_builder(
        drink_converter,
        total_quantity=100.0,
        avg=300.0,
        target=400.0,
        past_quantity=80.0,
        past_avg=past_avg,
    ).get_cards()[3]

    assert card.state == "low"
    assert card.note == f"{_('Last year')} {past_avg:.0f}"
    assert card.show_icon is True
    assert card.improving is improving
    # the card has an arrow, so its tooltip has to say what the arrow compares
    assert card.explanation == (
        f"ml {_('per calendar day')}",
        _("The arrow compares with last year, up to the same date."),
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
    assert card.explanation == (
        f"ml {_('per calendar day')}",
        _("The arrow compares with last year, up to the same date."),
    )


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


@pytest.mark.parametrize("index", range(5), ids=lambda i: f"card_{i}")
def test_a_card_with_no_data_reads_no_data(main_user, drink_converter, index):
    card = _card_builder(drink_converter).get_cards()[index]

    assert card.state == "empty"
    assert card.value == ""
    assert card.note == _("No data")


@pytest.mark.parametrize(
    "past, note, state, show_icon",
    [
        pytest.param(0.0, _("this year"), "neutral", False, id="alone"),
        pytest.param(80.0, f"{_('Last year')} 2.0", "worsening", True, id="last_year"),
    ],
)
def test_card_pure_alcohol_reads_the_year_total(
    main_user, drink_converter, past, note, state, show_icon
):
    card = _card_builder(
        drink_converter, total_quantity=100.0, past_quantity=past
    ).get_cards()[4]

    assert card.value == "2.5"  # 100 units -> 250 std av -> 2.5 L pure alcohol
    assert card.unit == "L"
    assert card.note == note
    assert card.state == state
    assert card.show_icon is show_icon


@pytest.mark.parametrize(
    "current_days, past_days, note, state",
    [
        # 4 drinking days out of the 10 elapsed, against 2 last year
        pytest.param(4, 2, f"{_('Last year')} 2", "worsening", id="more"),
        pytest.param(1, 2, f"{_('Last year')} 2", "improving", id="fewer"),
    ],
)
def test_card_drinking_days_reads_against_last_year(
    main_user, drink_converter, current_days, past_days, note, state
):
    current = [_row(date(1999, 1, i), 3) for i in range(1, current_days + 1)]
    past = [_row(date(1998, 1, i), 3) for i in range(1, past_days + 1)]

    card = _card_builder(
        drink_converter,
        total_quantity=100.0,
        frequency_stats=_frequency(current, past),
    ).get_cards()[1]

    assert card.value == str(current_days)
    assert card.note == note
    assert card.state == state
    assert card.show_icon is True


@pytest.mark.parametrize(
    "past_days, arrow_key",
    [
        pytest.param(
            1,
            (_("The arrow compares with last year, up to the same date."),),
            id="baseline",
        ),
        pytest.param(0, (), id="no_baseline"),
    ],
)
def test_card_drinking_days_explains_itself(
    main_user, drink_converter, past_days, arrow_key
):
    """A reading, a definition and a key to the arrow are three kinds of
    statement, so each is its own paragraph — the key only with a baseline."""
    current = [_row(date(1999, 1, i), 3) for i in range(1, 5)]
    past = [_row(date(1998, 1, i), 3) for i in range(1, past_days + 1)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current, past)
    ).get_cards()[1]

    assert card.explanation == (
        _("%(share)s%% of the year so far") % {"share": "40"},
        _("Calendar days with at least one Drink recorded."),
        *arrow_key,
    )


def test_card_drinking_days_note_on_a_year_already_over(main_user, drink_converter):
    # the year is finished, so the share is of all 365 days and nothing is "so far"
    current = [_row(date(1999, 1, i), 3) for i in range(1, 5)]

    card = _card_builder(
        drink_converter, frequency_stats=_frequency(current, today=date(2000, 6, 1))
    ).get_cards()[1]

    assert card.explanation[0] == _("%(share)s%% of the year") % {"share": "1"}


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


@pytest.mark.parametrize(
    "today, drinks, months",
    [
        pytest.param(
            "1999-06-01", [date(1999, 1, 10)], 6, id="running_year_ends_in_june"
        ),
        pytest.param(
            "2000-03-01", [date(1999, 1, 10)], 12, id="finished_year_runs_to_december"
        ),
        pytest.param("2000-03-01", [], 12, id="finished_year_without_drinks"),
    ],
)
def test_index_tab_build_charts_end_at_the_month_reached(
    main_user, today, drinks, months
):
    # a month the year has not reached is not a month with no Drinks in it
    for drink_date in drinks:
        DrinkFactory(date=drink_date, stdav=2.5)
    actual = IndexTab.build(main_user, 1999, date.fromisoformat(today))

    assert len(actual["chart_consumption"].data) == months
    assert len(actual["chart_quantity"].data) == months


def test_index_tab_build_frequency_cards_read_the_daily_rows(main_user):
    # two Drinks on one day and one on another: two Drinking days, not three
    # rows — the count DrinkStats' monthly rows could not have produced
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1999, 2, 20), stdav=5.0)
    DrinkFactory(date=date(1998, 1, 10), stdav=2.5)

    cards = IndexTab.build(main_user, 1999, date(1999, 6, 1))["cards"]

    assert cards[1].value == "2"
    assert cards[1].state == "worsening"  # 2 days against last year's 1


@pytest.mark.parametrize(
    "year, today, drink_type, quantity, value, unit, amount",
    [
        pytest.param(
            1999, "1999-06-01", "beer", 100, "100", "ml", "36,5 L", id="volume"
        ),
        # Std Av is read as typed: the figure keeps its decimal and carries no unit
        pytest.param(
            1999, "1999-06-01", "stdav", 2.5, "2.5", "", "912,5 Std Av", id="stdav"
        ),
        pytest.param(
            2000, "2001-03-01", "beer", 100, "100", "ml", "36,6 L", id="empty_leap_year"
        ),
    ],
)
def test_index_tab_build_limit_has_data(
    main_user, year, today, drink_type, quantity, value, unit, amount
):
    main_user.drink_type = drink_type
    target = DrinkTargetFactory(
        user=main_user, year=year, quantity=quantity, drink_type=drink_type
    )

    card = IndexTab.build(main_user, year, date.fromisoformat(today))["cards"][5]

    assert card.title == _("Daily limit")
    assert card.state == stat_card.NEUTRAL
    assert card.value == value
    assert card.unit == unit
    assert card.note == _("%(amount)s per year") % {"amount": amount}
    assert card.edit_url == reverse("drinks:target_update", kwargs={"pk": target.pk})


def test_index_tab_build_limit_no_target(main_user):
    card = IndexTab.build(main_user, 1999, date(1999, 6, 1))["cards"][5]

    assert card.title == _("Daily limit")
    assert card.state == stat_card.EMPTY
    assert card.value == ""
    assert card.note == _("No limit set")
    assert card.edit_url == reverse("drinks:target_new", kwargs={"tab": "index"})


def test_index_tab_build_states_last_year_only_as_far_as_today(main_user):
    """A Drink last November is past this June, so it is no part of the baseline
    the cards state — the Year boundary cuts it off."""
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1998, 1, 10), stdav=10.0)
    DrinkFactory(date=date(1998, 11, 20), stdav=100.0)

    cards = {
        card.title: card
        for card in IndexTab.build(main_user, 1999, date(1999, 6, 1))["cards"]
    }

    assert cards[_("Std drinks")].note == f"{_('Last year')} 10"


@pytest.mark.parametrize(
    "drink_type, avg, targets, limit, decimals",
    [
        # one 2.5 Std Av Drink is one 500 ml beer; Jan 1 to Jun 1 is 152 days,
        # so 500 / 152 ml and 2.5 / 152 Std Av a day
        pytest.param(
            "beer",
            3.28947,
            [{"quantity": 100}],
            {"amount": 100.0, "is_set": True},
            0,
            id="volume",
        ),
        pytest.param(
            "stdav",
            0.016447,
            [{"quantity": 2.5, "drink_type": "stdav"}],
            {"amount": 2.5, "is_set": True},
            1,
            id="stdav",
        ),
        pytest.param(
            "beer", 3.28947, [], {"amount": 0.0, "is_set": False}, 0, id="no_target"
        ),
    ],
)
def test_chart_consumption_carries_the_limit_and_the_year_average(
    main_user, drink_type, avg, targets, limit, decimals
):
    """No Drink Target is a state of its own, so the chart draws no limit."""
    main_user.drink_type = drink_type
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    for target in targets:
        DrinkTargetFactory(user=main_user, year=1999, **target)

    chart = IndexTab.build(main_user, 1999, date(1999, 6, 1))[
        "chart_consumption"
    ].as_dict

    assert chart["limit"] == limit
    # 1e-5 is tighter than a 153-day denominator's shift (2e-2 and 1e-4)
    assert chart["avg"] == pytest.approx(avg, abs=1e-5)
    assert chart["decimals"] == decimals


def test_index_tab_build_counts_days_dry_from_the_last_drink_not_after_today(
    main_user,
):
    DrinkFactory(date=date(1999, 1, 10), stdav=2.5)
    DrinkFactory(date=date(1999, 8, 1), stdav=2.5)

    card = IndexTab.build(main_user, 1999, date(1999, 6, 1))["cards"][0]

    assert card.value == "142"
    assert card.note == "1999-01-10"
