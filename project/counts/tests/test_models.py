import pytest

from ..factories import CountFactory, CountTypeFactory
from ..models import CountType

pytestmark = pytest.mark.django_db

# ---------------------------------------------------------------------------------------
#                                                                                   Count
# --------------------------------------------------------------------------------------
def test_count_str():
    actual = CountFactory.build()

    assert str(actual) == '1999-01-01: 1'


# ---------------------------------------------------------------------------------------
#                                                                              Count Type
# ---------------------------------------------------------------------------------------
def test_count_type_str():
    obj = CountTypeFactory.build()

    assert str(obj) == 'Count Type'


@pytest.mark.xfail
def test_count_type_unique_for_user(main_user):
    CountType.objects.create(title='T', user=main_user)
    CountType.objects.create(title='T', user=main_user)


def test_count_type_unique_for_users(main_user, second_user):
    CountType.objects.create(title='T', user=main_user)
    CountType.objects.create(title='T', user=second_user)
