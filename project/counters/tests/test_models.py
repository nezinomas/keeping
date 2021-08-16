from datetime import date

import pytest
from mock import patch

from ...users.factories import UserFactory
from ..factories import CounterFactory
from ..models import Counter

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _counters():
    CounterFactory(date=date(1999, 1, 1), quantity=1.0)
    CounterFactory(date=date(1999, 1, 1), quantity=1.5)
    CounterFactory(date=date(1999, 2, 1), quantity=2.0)
    CounterFactory(date=date(1999, 2, 1), quantity=1.0)

    # second user
    CounterFactory(
        date=date(1999, 2, 1),
        quantity=100.0,
        counter_type='X',
        user=UserFactory(username='XXX', email='x@x.x')
    )

    # second CounterType for same user
    CounterFactory(counter_type='Z')


@pytest.fixture()
def _different_users():
    CounterFactory()
    CounterFactory(counter_type='X')
    CounterFactory(counter_type='X', user=UserFactory(username='XXX', email='x@x.x'))


# ----------------------------------------------------------------------------
#                                                                      Counter
# ----------------------------------------------------------------------------
def test_counter_str():
    actual = CounterFactory.build()

    assert str(actual) == '1999-01-01: 1'


@patch('project.counters.managers.CounterQuerySet.counter_type', 'Counter Type')
def test_counter_related(_different_users):
    actual = Counter.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


@patch('project.counters.managers.CounterQuerySet.counter_type', 'Counter Type')
def test_counter_items(_different_users):
    actual = Counter.objects.items()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


@patch('project.counters.managers.CounterQuerySet.counter_type', 'X')
def test_items_with_user(_different_users):
    u = UserFactory(username='XXX', email='x@x.x')

    actual = Counter.objects.items(u)

    assert len(actual) == 1
    assert actual[0].user.username == 'XXX'


@patch('project.counters.managers.CounterQuerySet.counter_type', 'Counter Type')
def test_counter_year(_different_users):
    actual = list(Counter.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)
    assert actual[0].user.username == 'bob'


@patch('project.counters.managers.CounterQuerySet.counter_type', 'X')
def test_year_with_user(_different_users):
    u = UserFactory(username='XXX', email='x@x.x')

    actual = Counter.objects.year(1999, u)

    assert len(actual) == 1
    assert actual[0].user.username == 'XXX'


def test_counter_quantity_float():
    p = CounterFactory(quantity=0.5)

    p.full_clean()

    assert str(p) == '1999-01-01: 0.5'


def test_counter_quantity_int():
    p = CounterFactory(quantity=5)

    p.full_clean()

    assert str(p) == '1999-01-01: 5.0'

@patch('project.counters.managers.CounterQuerySet.counter_type', 'Counter Type')
def test_counter_order():
    CounterFactory(date=date(1999, 1, 1))
    CounterFactory(date=date(1999, 12, 1))

    actual = list(Counter.objects.year(1999))

    assert str(actual[0]) == '1999-12-01: 1.0'
    assert str(actual[1]) == '1999-01-01: 1.0'


@patch('project.counters.managers.CounterQuerySet.counter_type', 'Counter Type')
def test_counter_months_quantity_sum(_counters):
    actual = Counter.objects.sum_by_month(1999).values_list('qty', flat=True)

    expect = [2.5, 3.0]

    assert expect == pytest.approx(actual, rel=1e-2)

@patch('project.core.lib.utils.get_request_kwargs', return_value='counter-type')
def test_counter_months_quantity_sum_no_records_for_current_year(mck):
    CounterFactory(date=date(1970, 1, 1), quantity=1.0)
    CounterFactory(date=date(2000, 1, 1), quantity=1.5)

    # second user
    CounterFactory(
        date=date(1999, 1, 1),
        quantity=1.5,
        counter_type='xT',
        user=UserFactory(username='XXX', email='x@x.x'))

    actual = Counter.objects.sum_by_month(1999).values_list('qty', flat=True)

    expect = []

    assert expect == pytest.approx(actual, rel=1e-2)


@patch('project.counters.managers.CounterQuerySet.counter_type', 'Counter Type')
def test_counter_quantity_for_one_year(_counters):
    actual = list(Counter.objects.sum_by_year(year=1999))

    assert actual[0]['qty'] == 5.5


@patch('project.counters.managers.CounterQuerySet.counter_type', 'Counter Type')
def test_counter_quantity_for_all_years(_counters):
    CounterFactory(date=date(2020, 1, 1), quantity=10)
    CounterFactory(date=date(2020, 12, 1), quantity=5)

    actual = list(Counter.objects.sum_by_year())

    assert actual[0]['qty'] == 5.5
    assert actual[1]['qty'] == 15


@patch('project.counters.managers.CounterQuerySet.counter_type', 'Counter Type')
def test_counter_days_quantity_sum(_counters):
    actual = Counter.objects.sum_by_day(1999).values_list('qty', flat=True)

    expect = [2.5, 3.0]

    assert expect == pytest.approx(actual, rel=1e-2)


@patch('project.counters.managers.CounterQuerySet.counter_type', 'Counter Type')
def test_counter_days_quantity_sum_for_january(_counters):
    actual = Counter.objects.sum_by_day(1999, 1).values_list('qty', flat=True)

    expect = [2.5]

    assert expect == pytest.approx(actual, rel=1e-2)
