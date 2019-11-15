from datetime import date

import pytest
from django.core.validators import ValidationError
from freezegun import freeze_time

from ...auths.factories import UserFactory
from ..factories import DrinkFactory, DrinkTargetFactory
from ..models import Drink, DrinkTarget

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _drinks():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 2, 1), quantity=2.0)
    DrinkFactory(date=date(1999, 2, 1), quantity=1.0)
    DrinkFactory(
        date=date(1999, 2, 1),
        quantity=100.0,
        user=UserFactory(username='XXX')
    )


# ----------------------------------------------------------------------------
#                                                                        Drink
# ----------------------------------------------------------------------------
def test_drink_str():
    actual = DrinkFactory.build()

    assert str(actual) == '1999-01-01: 1'


def test_drink_related(get_user):
    DrinkFactory()
    DrinkFactory(user=UserFactory(username='XXX'))

    actual = Drink.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_items(get_user):
    DrinkFactory()
    DrinkFactory(user=UserFactory(username='XXX'))

    actual = Drink.objects.items()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_year(get_user):
    DrinkFactory()
    DrinkFactory(user=UserFactory(username='XXX'))

    actual = list(Drink.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)
    assert actual[0].user.username == 'bob'

def test_drink_quantity_float():
    p = DrinkFactory(quantity=0.5)

    p.full_clean()

    assert str(p) == '1999-01-01: 0.5'



def test_drink_quantity_int():
    p = DrinkFactory(quantity=5)

    p.full_clean()

    assert str(p) == '1999-01-01: 5.0'


def test_drink_order(get_user):
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(1999, 12, 1))

    actual = list(Drink.objects.year(1999))

    assert str(actual[0]) == '1999-12-01: 1.0'
    assert str(actual[1]) == '1999-01-01: 1.0'


def test_drink_months_consumsion(get_user, _drinks):
    actual = Drink.objects.month_sum(1999).values_list('per_month', flat=True)

    expect = [40.32, 53.57]

    assert expect == pytest.approx(actual, rel=1e-2)


def test_drink_months_quantity_sum(get_user, _drinks):
    actual = Drink.objects.month_sum(1999).values_list('sum', flat=True)

    expect = [2.5, 3.0]

    assert expect == pytest.approx(actual, rel=1e-2)


def test_drink_months_quantity_sum_no_records_for_current_year(get_user):
    DrinkFactory(date=date(1970, 1, 1), quantity=1.0)
    DrinkFactory(date=date(2000, 1, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5, user=UserFactory(username='XXX'))

    actual = Drink.objects.month_sum(1999).values_list('sum', flat=True)

    expect = []

    assert expect == pytest.approx(actual, rel=1e-2)


def test_drink_months_month_num(get_user, _drinks):
    actual = Drink.objects.month_sum(1999).values_list('month', flat=True)

    expect = [1, 2]

    assert expect == list(actual)


def test_drink_months_month_len(get_user, _drinks):
    actual = Drink.objects.month_sum(1999).values_list('monthlen', flat=True)

    expect = [31, 28]

    assert expect == list(actual)


@freeze_time('1999-11-01')
def test_drink_days_sum_november(get_user):
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 11, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 11, 1), quantity=111, user=UserFactory(username='XXX'))

    actual = Drink.objects.day_sum(1999)

    assert actual['qty'] == 2.5
    assert round(actual['per_day'], 2) == 4.1


@freeze_time('1999-01-03')
def test_drink_days_sum_january(get_user):
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=111, user=UserFactory(username='XXX'))
    DrinkFactory(date=date(1999, 11, 1), quantity=1.5)

    actual = Drink.objects.day_sum(1999)

    assert actual['qty'] == 1.0
    assert round(actual['per_day'], 2) == 166.67


@freeze_time('1999-01-03')
def test_drink_days_sum_no_records_for_selected_year(get_user):
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0, user=UserFactory(username='XXX'))
    DrinkFactory(date=date(1999, 11, 1), quantity=1.5)

    actual = Drink.objects.day_sum(1998)

    assert actual == {}



# ----------------------------------------------------------------------------
#                                                                 Drink Target
# ----------------------------------------------------------------------------
def test_drink_target_str():
    actual = DrinkTargetFactory.build()

    assert str(actual) == '1999: 100'


def test_drink_target_related(get_user):
    DrinkTargetFactory()
    DrinkTargetFactory(user=UserFactory(username='XXX'))

    actual = DrinkTarget.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_target_items(get_user):
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=2000, user=UserFactory(username='XXX'))

    actual = DrinkTarget.objects.items()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_target_year(get_user):
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=1999, user=UserFactory(username='XXX'))

    actual = list(DrinkTarget.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].user.username == 'bob'


def test_drink_target_year_positive():
    actual = DrinkTargetFactory.build(year=-2000)

    try:
        actual.full_clean()
    except ValidationError as e:
        assert 'year' in e.message_dict


@pytest.mark.xfail(raises=Exception)
def test_drink_target_year_unique():
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=1999)


def test_drink_target_ordering():
    DrinkTargetFactory(year=1970)
    DrinkTargetFactory(year=1999)

    actual = list(DrinkTarget.objects.all())

    assert str(actual[0]) == '1999: 100'
    assert str(actual[1]) == '1970: 100'
