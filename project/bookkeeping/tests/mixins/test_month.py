import string
from types import SimpleNamespace

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ....users.tests.factories import User, UserFactory
from ...mixins.month import MonthMixin

USER_MONTH = 7


def _get_month(month):
    class Dummy(MonthMixin):
        request = SimpleNamespace(
            GET={"month": month}, user=UserFactory.build(month=USER_MONTH)
        )

    return Dummy().get_month()


@given(month=st.integers(1, 12), as_text=st.booleans())
@example(month=1, as_text=False)
def test_get_month_reads_a_month_from_one_to_twelve(month, as_text):
    assert _get_month(str(month) if as_text else month) == month


@given(
    month=st.one_of(
        st.integers().filter(lambda number: number not in range(1, 13)),
        st.text(alphabet=string.ascii_letters),
        st.none(),
    )
)
@example(month=20)
@example(month="x")
@example(month=0)
@example(month="")
@example(month=None)
def test_get_month_falls_back_to_the_users_month(month):
    assert _get_month(month) == USER_MONTH


@pytest.mark.django_db
def test_set_month():
    class Dummy(MonthMixin):
        request = SimpleNamespace(GET={"month": 1}, user=UserFactory())

    Dummy().set_month()

    actual = User.objects.first()
    assert actual.month == 1
