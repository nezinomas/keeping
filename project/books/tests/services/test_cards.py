from datetime import date

import pytest
from django.urls import reverse

from ....core.lib import stat_card
from ...services.cards import Cards
from ..factories import BookFactory, BookTargetFactory

pytestmark = pytest.mark.django_db


def test_three_cards_in_order(main_user):
    BookFactory(started=date(1998, 12, 1), ended=date(1999, 1, 31))
    BookFactory()
    BookTargetFactory()

    actual = Cards.build(main_user, 1999)

    assert [x.title for x in actual] == ["Perskaitytos", "Skaitomos", "Tikslas"]
    assert [x.value for x in actual] == ["1", "1", "100"]


def test_no_card_carries_a_note(main_user):
    """A note explains a figure against something else; these stand on their own."""
    BookFactory()
    BookTargetFactory()

    actual = Cards.build(main_user, 1999)

    assert [x.note for x in actual] == ["", "", ""]


def test_no_card_is_judged(main_user):
    """The three figures are facts about the Reading year, not verdicts on it."""
    BookFactory()
    BookTargetFactory()

    actual = Cards.build(main_user, 1999)

    assert [x.state for x in actual] == [stat_card.NEUTRAL] * 3
    assert [x.show_icon for x in actual] == [False] * 3
    assert [x.unit for x in actual] == ["", "", ""]


def test_finished_counts_the_year_a_book_ended_in(main_user):
    """A book carried across New Year belongs to the year it was finished."""
    BookFactory(started=date(1998, 6, 1), ended=date(1999, 2, 1))

    assert Cards.build(main_user, 1998)[0].value == "0"
    assert Cards.build(main_user, 1999)[0].value == "1"


def test_finished_with_no_books(main_user):
    """Zero is something to show: the year finished none, and says so."""
    actual = Cards.build(main_user, 1999)[0]

    assert actual.value == "0"
    assert actual.state == stat_card.NEUTRAL


def test_reading_counts_every_open_book_started_by_the_year(main_user):
    BookFactory(started=date(1997, 1, 1))
    BookFactory(started=date(1999, 5, 1))
    BookFactory(started=date(1999, 6, 1), ended=date(1999, 7, 1))

    assert Cards.build(main_user, 1999)[1].value == "2"


def test_reading_with_no_books(main_user):
    assert Cards.build(main_user, 1999)[1].value == "0"


def test_goal_card_with_no_target(main_user):
    actual = Cards.build(main_user, 1999)[2]

    assert actual.state == stat_card.EMPTY
    assert actual.value == ""
    assert actual.note == "Neįvestas tikslas"


def test_goal_card_reads_the_selected_year(main_user):
    BookTargetFactory(year=1998, quantity=12)
    BookTargetFactory(year=1999, quantity=34)

    assert Cards.build(main_user, 1998)[2].value == "12"
    assert Cards.build(main_user, 1999)[2].value == "34"


def test_goal_card_pencil_opens_target_new(main_user):
    actual = Cards.build(main_user, 1999)[2]

    assert actual.edit_url == reverse("books:target_new")


def test_goal_card_pencil_opens_target_update(main_user):
    target = BookTargetFactory()

    actual = Cards.build(main_user, 1999)[2]

    assert actual.edit_url == reverse("books:target_update", kwargs={"pk": target.pk})
