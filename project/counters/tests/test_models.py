from datetime import date

import pytest

from ...users.factories import UserFactory
from ..factories import CounterFactory, CounterTypeFactory
from ..models import Counter, CounterType

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _counters():
    CounterFactory(date=date(1999, 1, 1), quantity=1.0)
    CounterFactory(date=date(1999, 1, 1), quantity=1.5)
    CounterFactory(date=date(1999, 2, 1), quantity=2.0)
    CounterFactory(date=date(1999, 2, 1), quantity=1.0)

    # second user
    ct = CounterTypeFactory(title='xT', user=UserFactory(username='XXX'))
    CounterFactory(
        date=date(1999, 2, 1),
        quantity=100.0,
        counter_type=ct
    )


@pytest.fixture()
def _different_users():
    CounterFactory()
    CounterFactory(counter_type=CounterTypeFactory(title='xT', user=UserFactory(username='XXX')))


# ----------------------------------------------------------------------------
#                                                                 Counter Type
# ----------------------------------------------------------------------------
def test_counter_type_str():
    actual = CounterTypeFactory.build()

    assert str(actual) == 'Counter Type'


def test_counter_type_user():
    actual = CounterTypeFactory()

    assert actual.user.username == 'bob'


def test_counter_type_items(get_user):
    CounterTypeFactory(title='T1')
    CounterTypeFactory(title='T2')

    actual = CounterType.objects.related()

    assert actual.count() == 2


def test_counter_type_items_user(get_user):
    CounterTypeFactory(title='T1', user=UserFactory())
    CounterTypeFactory(title='T2', user=UserFactory(username='u2'))

    actual = CounterType.objects.related()

    assert actual.count() == 1


def test_counter_type_related_qs_count(django_assert_max_num_queries, get_user):
    CounterTypeFactory(title='T1')
    CounterTypeFactory(title='T2')
    CounterTypeFactory(title='T3')

    with django_assert_max_num_queries(2):
        list(q.title for q in CounterType.objects.related())


@pytest.mark.xfail
def test_counter_type_unique_user(get_user):
    CounterType.objects.create(title='T1', user=UserFactory())
    CounterType.objects.create(title='T1', user=UserFactory())


def test_counter_type_unique_users(get_user):
    CounterType.objects.create(title='T1', user=UserFactory(username='x'))
    CounterType.objects.create(title='T1', user=UserFactory(username='y'))


def test_counter_type_ordering(get_user):
    CounterTypeFactory(title='z')
    CounterTypeFactory(title='a')

    actual = CounterType.objects.related()

    assert list(actual.values_list('title', flat=True)) == ['a', 'z']


# ----------------------------------------------------------------------------
#                                                                      Counter
# ----------------------------------------------------------------------------
def test_counter_str():
    actual = CounterFactory.build()

    assert str(actual) == '1999-01-01: 1'


def test_counter_related(get_user, _different_users):
    actual = Counter.objects.related()

    assert len(actual) == 1
    assert actual[0].counter_type.user.username == 'bob'


def test_counter_items(get_user, _different_users):
    actual = Counter.objects.items()

    assert len(actual) == 1
    assert actual[0].counter_type.user.username == 'bob'


def test_counter_year(get_user, _different_users):
    actual = list(Counter.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)
    assert actual[0].counter_type.user.username == 'bob'


def test_counter_quantity_float():
    p = CounterFactory(quantity=0.5)

    p.full_clean()

    assert str(p) == '1999-01-01: 0.5'


def test_counter_quantity_int():
    p = CounterFactory(quantity=5)

    p.full_clean()

    assert str(p) == '1999-01-01: 5.0'


def test_counter_order(get_user):
    CounterFactory(date=date(1999, 1, 1))
    CounterFactory(date=date(1999, 12, 1))

    actual = list(Counter.objects.year(1999))

    assert str(actual[0]) == '1999-12-01: 1.0'
    assert str(actual[1]) == '1999-01-01: 1.0'


def test_counter_months_quantity_sum(get_user, _counters):
    actual = Counter.objects.sum_by_month(1999).values_list('qty', flat=True)

    expect = [2.5, 3.0]

    assert expect == pytest.approx(actual, rel=1e-2)


def test_counter_months_quantity_sum_no_records_for_current_year(get_user):
    CounterFactory(date=date(1970, 1, 1), quantity=1.0)
    CounterFactory(date=date(2000, 1, 1), quantity=1.5)

    # second user
    ct = CounterTypeFactory(title='xT', user=UserFactory(username='XXX'))
    CounterFactory(date=date(1999, 1, 1), quantity=1.5, counter_type=ct)

    actual = Counter.objects.sum_by_month(1999).values_list('qty', flat=True)

    expect = []

    assert expect == pytest.approx(actual, rel=1e-2)


def test_counter_quantity_for_one_year(get_user, _counters):
    actual = list(Counter.objects.sum_by_year(year=1999))

    assert actual[0]['qty'] == 5.5


def test_counter_quantity_for_all_years(get_user, _counters):
    CounterFactory(date=date(2020, 1, 1), quantity=10)
    CounterFactory(date=date(2020, 12, 1), quantity=5)

    actual = list(Counter.objects.sum_by_year())

    assert actual[0]['qty'] == 5.5
    assert actual[1]['qty'] == 15
