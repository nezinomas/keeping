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

    assert str(actual) == 'Journal'


@pytest.mark.disable_get_user_patch
def test_journal_has_many_users():
    jr = JournalFactory(title='T')
    UserFactory(username='X', journal=jr)
    UserFactory(username='Y', journal=jr)

    actual = Journal.objects.get(pk=jr.pk)

    assert actual.users.count() == 2
