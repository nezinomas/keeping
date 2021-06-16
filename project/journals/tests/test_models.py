import pytest

from ...users.factories import UserFactory
from ...users.models import User
from ..factories import JournalFactory
from ..models import Journal

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                 Journal
# ---------------------------------------------------------------------------------------
def test_journal_str():
    actual = JournalFactory.build()

    assert str(actual) == 'bob Journal'


def test_journal_username():
    b = JournalFactory()
    actual = Journal.objects.get(pk=b.pk)

    assert actual.user.username == 'bob'


def test_journal_reversed():
    u = UserFactory()
    JournalFactory()

    actual = User.objects.get(pk=u.pk)

    assert actual.journal.count() == 1
    assert str(actual.journal.first()) == 'bob Journal'


def test_journal_related():
    obj = JournalFactory()

    actual = Journal.objects.related()

    assert str(actual[0]) == str(obj)


def test_journal_related_queries(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Journal.objects.related().values()
