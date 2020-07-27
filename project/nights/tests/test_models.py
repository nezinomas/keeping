from datetime import date

import pytest
from mock import patch

from ...users.factories import UserFactory
from ..factories import NightFactory
from ..models import Night

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _second_user():
    return NightFactory(counter_type='Z', user=UserFactory(username='XXX'))


@pytest.fixture()
def _nights(_second_user):
    NightFactory(date=date(1999, 1, 1), quantity=1.0)
    NightFactory(date=date(1999, 1, 1), quantity=1.5)
    NightFactory(date=date(1999, 2, 1), quantity=2.0)
    NightFactory(date=date(1999, 2, 1), quantity=1.0)

    NightFactory(date=date(1999, 1, 1), quantity=1.0, counter_type='Z')


@pytest.fixture()
def _different_users(_second_user):
    NightFactory()
    NightFactory(counter_type=_second_user)


# ----------------------------------------------------------------------------
#                                                                        Night
# ----------------------------------------------------------------------------
def test_night_str():
    actual = NightFactory.build()

    assert str(actual) == '1999-01-01: 1'
