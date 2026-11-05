from datetime import date

import pytest

from ....core.lib.stat_card import EMPTY, NEUTRAL
from ...services.cards import HistoryCards, OverviewCards
from ...services.counter_life import CounterLife
from ..factories import CountFactory, CountTypeFactory

pytestmark = pytest.mark.django_db

TODAY = date(1999, 7, 12)


def _overview(user, today):
    return OverviewCards.build(CounterLife.read(user, "count-type", today))


def _history(user, today):
    return HistoryCards.build(CounterLife.read(user, "count-type", today))


@pytest.mark.parametrize(
    "build, titles",
    [
        pytest.param(_overview, ["Šiais metais", "Iš viso", "Tarpas"], id="overview"),
        pytest.param(_history, ["Iš viso", "Metų", "Vidutiniai metai"], id="history"),
    ],
)
def test_has_three_cards_in_order(main_user, build, titles):
    CountTypeFactory()

    assert [card.title for card in build(main_user, TODAY)] == titles


def test_overview_states_the_year_the_total_and_the_current_gap(main_user):
    CountFactory(date=date(1998, 5, 1), quantity=2)
    CountFactory(date=date(1999, 1, 1), quantity=3)
    CountFactory(date=date(1999, 7, 8), quantity=4)

    year, total, gap = _overview(main_user, TODAY)

    assert year.value == "7"
    assert total.value == "9"
    assert gap.value == "4"


def test_overview_gap_notes_the_typical_gap(main_user):
    CountFactory(date=date(1999, 1, 1))
    CountFactory(date=date(1999, 1, 11))
    CountFactory(date=date(1999, 1, 31))

    assert _overview(main_user, TODAY)[2].note == "įprastai 15 d."


def test_overview_gap_explains_what_it_counts(main_user):
    CountFactory()

    assert _overview(main_user, TODAY)[2].explanation == (
        "Dienos nuo paskutinio įrašo",
    )


def test_overview_year_and_total_carry_no_explanation(main_user):
    CountFactory()

    year, total, _gap = _overview(main_user, TODAY)

    assert year.explanation == ()
    assert total.explanation == ()
    assert year.note == ""


@pytest.mark.parametrize(
    "build, index, note",
    [
        pytest.param(_overview, 0, "1999 metais įrašų nėra.", id="this_year"),
        pytest.param(_history, 1, "Įrašų nėra", id="years"),
    ],
)
def test_an_empty_card_notes_what_it_lacks(main_user, build, index, note):
    CountTypeFactory()

    assert build(main_user, TODAY)[index].note == note


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_overview, id="overview"),
        pytest.param(_history, id="history"),
    ],
)
def test_a_counter_with_no_records_has_empty_cards(main_user, build):
    CountTypeFactory()

    assert [card.state for card in build(main_user, TODAY)] == [EMPTY] * 3


def test_overview_year_is_empty_when_the_year_has_no_records(main_user):
    CountFactory(date=date(1998, 5, 1))

    year, total, _gap = _overview(main_user, TODAY)

    assert year.state == EMPTY
    assert total.state == NEUTRAL
    assert total.value == "1"


def test_overview_gap_is_empty_on_a_finished_year(main_user):
    CountFactory(date=date(1999, 1, 1))
    CountFactory(date=date(1999, 1, 11))

    gap = _overview(main_user, today=date(2001, 7, 12))[2]

    assert gap.state == EMPTY
    assert gap.note == "įprastai 10 d."


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_overview, id="overview"),
        pytest.param(_history, id="history"),
    ],
)
def test_cards_carry_no_tone_no_unit_and_no_pencil(main_user, build):
    CountFactory()

    for card in build(main_user, TODAY):
        assert card.state in (NEUTRAL, EMPTY)
        assert card.unit == ""
        assert card.edit_url == ""
        assert not card.show_icon


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_overview, id="overview"),
        pytest.param(_history, id="history"),
    ],
)
def test_a_tab_reads_the_counter_in_one_query(
    main_user, build, django_assert_num_queries
):
    CountFactory()

    with django_assert_num_queries(1):
        build(main_user, TODAY)


@pytest.mark.parametrize(
    "build, index",
    [
        pytest.param(_overview, 1, id="overview"),
        pytest.param(_history, 0, id="history"),
    ],
)
def test_total_ever_is_every_record_since_the_first_year(main_user, build, index):
    CountFactory(date=date(1996, 1, 1), quantity=2)
    CountFactory(date=date(1998, 1, 1), quantity=3)

    total = build(main_user, TODAY)[index]

    assert total.value == "5"
    assert total.note == "nuo 1996"


def test_history_years_counts_years_with_records_not_years_in_the_span(main_user):
    CountFactory(date=date(1996, 1, 1))
    CountFactory(date=date(1998, 1, 1))

    years = _history(main_user, TODAY)[1]

    assert years.value == "2"
    assert years.note == "1996–1998"
    assert years.explanation == ("Metai, kuriais yra bent vienas įrašas",)


def test_history_years_of_a_single_year_notes_that_year_alone(main_user):
    CountFactory(date=date(1996, 1, 1))

    assert _history(main_user, TODAY)[1].note == "1996"


def test_history_median_year_takes_the_finished_years_median(main_user):
    CountFactory(date=date(1996, 1, 1), quantity=1)
    CountFactory(date=date(1997, 1, 1), quantity=3)
    CountFactory(date=date(1998, 1, 1), quantity=4)
    CountFactory(date=date(1999, 1, 1), quantity=99)

    median = _history(main_user, TODAY)[2]

    assert median.value == "3"
    assert median.note == "nuo 1 iki 4"
    assert median.explanation == ("Metinių sumų mediana",)


def test_history_median_year_is_empty_when_no_year_has_finished(main_user):
    CountFactory(date=date(1999, 1, 1))

    assert _history(main_user, TODAY)[2].state == EMPTY
