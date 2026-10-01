from datetime import date

import pytest

from ...expenses.tests.factories import ExpenseFactory
from ...users.tests.factories import UserFactory
from ..models import Journal
from .factories import JournalFactory

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                               Journal
# -------------------------------------------------------------------------------------
def test_journal_str():
    actual = JournalFactory.build()

    assert str(actual) == "bob Journal"


@pytest.mark.disable_get_user_patch
def test_journal_has_many_users():
    jr = JournalFactory(title="T")

    UserFactory(username="X", email="x@x.x", journal=jr)
    UserFactory(username="Y", email="y@y.y", journal=jr)

    actual = Journal.objects.get(pk=jr.pk)

    assert actual.users.count() == 2


def test_journal_first_record_update_on_expense_save():
    ExpenseFactory(date=date(1974, 1, 1))

    actual = Journal.objects.first().first_record

    assert actual == date(1974, 1, 1)


def test_journal_title_slug_not_checked_against_other_journals():
    JournalFactory(title="Būstas")
    journal = JournalFactory.build(title="Bustas")

    journal.full_clean()


@pytest.mark.parametrize(
    "username, expect",
    [
        ("bob", "bob Journal"),
        ("jonas+test@mail.lt", "jonastestmail.lt Journal"),
        ("@+@", "Journal"),
        ("ﬃx", "x Journal"),
    ],
)
def test_journal_title_for_username(username, expect):
    assert Journal.title_for(username) == expect


def test_journal_title_for_username_passes_title_rules():
    journal = Journal(title=Journal.title_for("jonas+test@mail.lt"))

    journal.full_clean()


def test_journal_title_for_long_username_fits_title():
    max_length = Journal._meta.get_field("title").max_length

    actual = Journal.title_for("a" * 150)

    assert len(actual) == max_length
    assert actual.endswith("a Journal")
