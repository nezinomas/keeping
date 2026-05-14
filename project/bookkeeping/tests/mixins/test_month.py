from types import SimpleNamespace

import pytest

from ....users.tests.factories import User, UserFactory
from ...mixins.month import MonthMixin


@pytest.mark.parametrize(
    "month, expect",
    [
        (1, 1),
        (20, 12),
        ("x", 12),
        (0, 12),
        ("", 12),
        (None, 12),
    ],
)
def test_get_month(month, expect):
    class Dummy(MonthMixin):
        request = SimpleNamespace(GET={"month": month}, user=UserFactory.build())

    actual = Dummy().get_month()
    assert actual == expect


@pytest.mark.django_db
def test_set_month():
    class Dummy(MonthMixin):
        request = SimpleNamespace(GET={"month": 1}, user=UserFactory())

    Dummy().set_month()

    actual = User.objects.first()
    assert actual.month == 1
