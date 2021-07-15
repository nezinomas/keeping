from datetime import date

import pytest

from ...expenses.factories import ExpenseFactory
from ...journals.models import Journal
from ...users.factories import UserFactory
from ..factories import JournalFactory
from ..models import Journal

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                 Journal
# ---------------------------------------------------------------------------------------
def test_journal_str():
    actual = JournalFactory.build()

    assert str(actual) == 'bob Journal'


@pytest.mark.disable_get_user_patch
def test_journal_has_many_users():
    jr = JournalFactory(title='T')

    UserFactory(username='X', journal=jr)
    UserFactory(username='Y', journal=jr)

    actual = Journal.objects.get(pk=jr.pk)

    assert actual.users.count() == 2


def test_journal_first_record_update_on_expense_save():
    ExpenseFactory(date=date(1974, 1, 1))

    actual = Journal.objects.first().first_record

    assert actual == date(1974, 1, 1)
