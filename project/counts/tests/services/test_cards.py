from datetime import date, datetime

import pytest
import time_machine

from ....core.lib.stat_card import EMPTY, NEUTRAL
from ...services.cards import HistoryCards, OverviewCards
from ...services.counter_life import CounterLife
from ..factories import CountFactory, CountTypeFactory

pytestmark = pytest.mark.django_db


def _overview(user):
    return OverviewCards.build(CounterLife.read(user, "count-type"))


def _history(user):
    return HistoryCards.build(CounterLife.read(user, "count-type"))


@pytest.mark.parametrize(
    "build, titles",
    [
        pytest.param(_overview, ["Šiais metais", "Iš viso", "Tarpas"], id="overview"),
        pytest.param(_history, ["Iš viso", "Metų", "Vidutiniai metai"], id="history"),
    ],
)
@time_machine.travel(datetime(1999, 7, 12))
def test_has_three_cards_in_order(main_user, build, titles):
    CountTypeFactory()

    assert [card.title for card in build(main_user)] == titles


@time_machine.travel(datetime(1999, 7, 12))
def test_overview_states_the_year_the_total_and_the_current_gap(main_user):
    CountFactory(date=date(1998, 5, 1), quantity=2)
    CountFactory(date=date(1999, 1, 1), quantity=3)
    CountFactory(date=date(1999, 7, 8), quantity=4)

    year, total, gap = _overview(main_user)

    assert year.value == "7"
    assert total.value == "9"
    assert gap.value == "4"


@time_machine.travel(datetime(1999, 7, 12))
def test_overview_total_notes_the_year_of_the_first_record(main_user):
    CountFactory(date=date(1998, 5, 1))
    CountFactory(date=date(1999, 1, 1))

    assert _overview(main_user)[1].note == "nuo 1998"


@time_machine.travel(datetime(1999, 7, 12))
def test_overview_gap_notes_the_typical_gap(main_user):
    CountFactory(date=date(1999, 1, 1))
    CountFactory(date=date(1999, 1, 11))
    CountFactory(date=date(1999, 1, 31))

    assert _overview(main_user)[2].note == "įprastai 15 d."


@time_machine.travel(datetime(1999, 7, 12))
def test_overview_gap_explains_what_it_counts(main_user):
    CountFactory()

    assert _overview(main_user)[2].explanation == ("Dienos nuo paskutinio įrašo",)


@time_machine.travel(datetime(1999, 7, 12))
def test_overview_year_and_total_carry_no_explanation(main_user):
    CountFactory()

    year, total, _gap = _overview(main_user)

    assert year.explanation == ()
    assert total.explanation == ()
    assert year.note == ""


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_overview, id="overview"),
        pytest.param(_history, id="history"),
    ],
)
@time_machine.travel(datetime(1999, 7, 12))
def test_a_counter_with_no_records_has_empty_cards(main_user, build):
    CountTypeFactory()

    assert [card.state for card in build(main_user)] == [EMPTY] * 3


@time_machine.travel(datetime(1999, 7, 12))
def test_overview_year_is_empty_when_the_year_has_no_records(main_user):
    CountFactory(date=date(1998, 5, 1))

    year, total, _gap = _overview(main_user)

    assert year.state == EMPTY
    assert total.state == NEUTRAL
    assert total.value == "1"


@time_machine.travel(datetime(2001, 7, 12))
def test_overview_gap_is_empty_on_a_finished_year(main_user):
    CountFactory(date=date(1999, 1, 1))
    CountFactory(date=date(1999, 1, 11))

    gap = _overview(main_user)[2]

    assert gap.state == EMPTY
    assert gap.note == "įprastai 10 d."


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_overview, id="overview"),
        pytest.param(_history, id="history"),
    ],
)
@time_machine.travel(datetime(1999, 7, 12))
def test_cards_carry_no_tone_no_unit_and_no_pencil(main_user, build):
    CountFactory()

    for card in build(main_user):
        assert card.state in (NEUTRAL, EMPTY)
        assert card.unit == ""
        assert card.edit_url == ""
        assert not card.show_icon


@time_machine.travel(datetime(1999, 7, 12))
def test_overview_reads_the_counter_in_one_query(main_user, django_assert_num_queries):
    CountFactory()

    with django_assert_num_queries(1):
        _overview(main_user)


@time_machine.travel(datetime(1999, 7, 12))
def test_history_total_is_every_record_the_counter_holds(main_user):
    CountFactory(date=date(1996, 1, 1), quantity=2)
    CountFactory(date=date(1998, 1, 1), quantity=3)

    total = _history(main_user)[0]

    assert total.value == "5"
    assert total.note == "nuo 1996"


@time_machine.travel(datetime(1999, 7, 12))
def test_history_years_counts_years_with_records_not_years_in_the_span(main_user):
    CountFactory(date=date(1996, 1, 1))
    CountFactory(date=date(1998, 1, 1))

    years = _history(main_user)[1]

    assert years.value == "2"
    assert years.note == "1996–1998"
    assert years.explanation == ("Metai, kuriais yra bent vienas įrašas",)


@time_machine.travel(datetime(1999, 7, 12))
def test_history_years_of_a_single_year_notes_that_year_alone(main_user):
    CountFactory(date=date(1996, 1, 1))

    assert _history(main_user)[1].note == "1996"


@time_machine.travel(datetime(1999, 7, 12))
def test_history_median_year_takes_the_median_of_the_yearly_totals(main_user):
    CountFactory(date=date(1996, 1, 1), quantity=1)
    CountFactory(date=date(1997, 1, 1), quantity=3)
    CountFactory(date=date(1998, 1, 1), quantity=4)

    median = _history(main_user)[2]

    assert median.value == "3"
    assert median.note == "nuo 1 iki 4"
    assert median.explanation == ("Metinių sumų mediana",)


@time_machine.travel(datetime(1999, 7, 12))
def test_history_median_year_ignores_the_running_year(main_user):
    CountFactory(date=date(1996, 1, 1), quantity=1)
    CountFactory(date=date(1997, 1, 1), quantity=3)
    CountFactory(date=date(1998, 1, 1), quantity=4)
    CountFactory(date=date(1999, 1, 1), quantity=99)

    median = _history(main_user)[2]

    assert median.value == "3"
    assert median.note == "nuo 1 iki 4"


@time_machine.travel(datetime(1999, 7, 12))
def test_history_median_year_is_empty_when_no_year_has_finished(main_user):
    CountFactory(date=date(1999, 1, 1))

    assert _history(main_user)[2].state == EMPTY


@time_machine.travel(datetime(1999, 7, 12))
def test_history_reads_the_counter_in_one_query(main_user, django_assert_num_queries):
    CountFactory()

    with django_assert_num_queries(1):
        _history(main_user)
