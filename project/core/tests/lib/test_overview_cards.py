from datetime import date

import pytest

from ....core.lib.overview_cards import OverviewCards
from ....core.lib.stat_card import EMPTY, NEUTRAL, EmptyStatCard
from ....core.lib.year_boundary import YearBoundary

RUNNING = YearBoundary(year=2026, today=date(2026, 9, 15))
FINISHED = YearBoundary(year=2025, today=date(2026, 9, 15))
COMING = YearBoundary(year=2027, today=date(2026, 9, 15))

YEAR = [{"title": "Alga", "sum": 90_000}, {"title": "Kita", "sum": 30_000}]
LAST_YEAR = [{"title": "Alga", "sum": 80_000}]
EXPLANATION = "Paaiškinimas"


def _cards(boundary=RUNNING, year=YEAR, last_year=LAST_YEAR):
    return {
        card.title: card
        for card in OverviewCards.build(year, last_year, boundary, EXPLANATION)
    }


def test_three_cards_in_order():
    assert list(_cards()) == ["Šiais metais", "Per mėnesį", "Didžiausia rūšis"]


@pytest.mark.parametrize(
    "last_year, note",
    [
        pytest.param(LAST_YEAR, "Pernai 800", id="last-year"),
        pytest.param([], "", id="no-last-year"),
    ],
)
def test_this_year_is_the_total_in_euro_noting_last_year(last_year, note):
    card = _cards(last_year=last_year)["Šiais metais"]

    assert (card.value, card.note) == ("1.200", note)


@pytest.mark.parametrize(
    "boundary, value, note",
    [
        pytest.param(RUNNING, "133", "9 mėnesiai", id="running"),
        pytest.param(FINISHED, "100", "12 mėnesių", id="finished"),
    ],
)
def test_per_month_divides_the_year_by_the_months_reached(boundary, value, note):
    card = _cards(boundary=boundary)["Per mėnesį"]

    assert (card.value, card.note, card.explanation) == (
        value,
        note,
        ("Metų suma, padalinta iš prabėgusių mėnesių",),
    )


def test_per_month_of_a_coming_year_is_empty_while_this_year_reads_the_total():
    cards = _cards(boundary=COMING)

    assert cards["Per mėnesį"] == EmptyStatCard("Per mėnesį")
    assert cards["Šiais metais"].value == "1.200"


@pytest.mark.parametrize(
    ("year", "note"),
    [
        (YEAR, "75% metų sumos"),
        (
            [{"title": "Alga", "sum": 99_700}, {"title": "Kita", "sum": 300}],
            "> 99% metų sumos",
        ),
    ],
    ids=["share", "near_the_whole"],
)
def test_largest_type_names_the_type_and_its_share(year, note):
    card = _cards(year=year)["Didžiausia rūšis"]

    assert card.value == "Alga"
    assert card.note == note
    assert card.explanation == (EXPLANATION,)


def test_an_empty_year_is_three_empty_cards():
    cards = _cards(year=[]).values()

    assert [card.state for card in cards] == [EMPTY] * 3
    assert all("0" not in f"{card.value}{card.note}" for card in cards)


def test_no_card_carries_a_state_or_an_arrow():
    cards = _cards().values()

    assert [card.state for card in cards] == [NEUTRAL] * 3
    assert not any(card.show_icon for card in cards)
