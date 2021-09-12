import pytest

from ..factories import UserFactory
from ..models import User

pytestmark = pytest.mark.django_db


def test_user_str():
    actual = UserFactory.build()

    assert str(actual) == 'bob'


def test_user_reversed():
    actual = User.objects.first()

    assert User.objects.count() == 1
    assert str(actual.journal) == 'bob Journal'


def test_user_related_queries(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(x.journal.title for x in User.objects.related())
