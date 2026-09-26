from datetime import date

from ....core.lib.stat_card import EMPTY, NEUTRAL
from ....core.lib.year_boundary import YearBoundary
from ...services.cards import OverviewCards

RUNNING = YearBoundary(year=2026, today=date(2026, 9, 15))
FINISHED = YearBoundary(year=2025, today=date(2026, 9, 15))

YEAR = [{"title": "Alga", "sum": 90_000}, {"title": "Kita", "sum": 30_000}]
LAST_YEAR = [{"title": "Alga", "sum": 80_000}]


def _cards(boundary=RUNNING, year=YEAR, last_year=LAST_YEAR):
    return {card.title: card for card in OverviewCards.build(year, last_year, boundary)}


def test_three_cards_in_order():
    assert list(_cards()) == ["Šiais metais", "Per mėnesį", "Didžiausia rūšis"]


def test_this_year_is_the_total_in_euro():
    card = _cards()["Šiais metais"]

    assert card.value == "1.200"
    assert card.note == "Pernai 800"


def test_this_year_has_no_note_when_last_year_is_empty():
    assert _cards(last_year=[])["Šiais metais"].note == ""


def test_per_month_divides_a_running_year_by_the_months_reached():
    card = _cards()["Per mėnesį"]

    assert card.value == "133"
    assert card.note == "9 mėnesiai"
    assert card.explanation == ("Metų suma, padalinta iš prabėgusių mėnesių",)


def test_per_month_divides_a_finished_year_by_twelve():
    card = _cards(boundary=FINISHED)["Per mėnesį"]

    assert card.value == "100"
    assert card.note == "12 mėnesių"


def test_largest_type_names_the_type_and_its_share():
    card = _cards()["Didžiausia rūšis"]

    assert card.value == "Alga"
    assert card.note == "75% metų sumos"
    assert card.explanation == ("Didžiausią šių metų dalį sudaranti pajamų rūšis",)


def test_an_empty_year_is_three_empty_cards():
    cards = _cards(year=[]).values()

    assert [card.state for card in cards] == [EMPTY] * 3
    assert all("0" not in f"{card.value}{card.note}" for card in cards)


def test_no_card_carries_a_state_or_an_arrow():
    cards = _cards().values()

    assert [card.state for card in cards] == [NEUTRAL] * 3
    assert not any(card.show_icon for card in cards)
