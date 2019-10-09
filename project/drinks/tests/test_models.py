from datetime import date

import pytest
from django.core.validators import ValidationError
from freezegun import freeze_time

from ..factories import DrinkFactory, DrinkTargetFactory
from ..models import Drink, DrinkTarget


@pytest.fixture()
def drinks():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 2, 1), quantity=2.0)
    DrinkFactory(date=date(1999, 2, 1), quantity=1.0)


def test_drink_str():
    actual = DrinkFactory.build()

    assert '1999-01-01: 1' == str(actual)


@pytest.mark.django_db
def test_drink_year():
    DrinkFactory()

    actual = list(Drink.objects.year(1999))

    assert 1 == len(actual)
    assert date(1999, 1, 1) == actual[0].date


def test_drink_quantity_float():
    p = DrinkFactory.build(quantity=0.5)

    p.full_clean()

    assert '1999-01-01: 0.5' == str(p)


def test_drink_quantity_int():
    p = DrinkFactory.build(quantity=5)

    p.full_clean()

    assert '1999-01-01: 5.0' == str(p)


@pytest.mark.django_db()
def test_drink_order():
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(1999, 12, 1))

    actual = list(Drink.objects.year(1999))

    assert '1999-12-01: 1.0' == str(actual[0])
    assert '1999-01-01: 1.0' == str(actual[1])


def test_drink_target_str():
    actual = DrinkTargetFactory.build()

    assert '1999: 100' == str(actual)


def test_drink_target_year_positive():
    actual = DrinkTargetFactory.build(year=-2000)

    try:
        actual.full_clean()
    except ValidationError as e:
        assert 'year' in e.message_dict


@pytest.mark.django_db
@pytest.mark.xfail(raises=Exception)
def test_drink_target_year_unique():
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=1999)


@pytest.mark.django_db
def test_drink_target_ordering():
    DrinkTargetFactory(year=1970)
    DrinkTargetFactory(year=1999)

    actual = list(DrinkTarget.objects.all())

    assert '1999: 100' == str(actual[0])
    assert '1970: 100' == str(actual[1])


@pytest.mark.django_db
def test_drink_target_year():
    DrinkTargetFactory(year=1970)

    actual = list(DrinkTarget.objects.year(1970))

    assert 1 == len(actual)
    assert 1970 == actual[0].year


@pytest.mark.django_db
def test_drink_months_consumsion(drinks):
    actual = Drink.objects.month_sum(1999).values_list('per_month', flat=True)

    expect = [40.32, 53.57]

    assert expect == pytest.approx(actual, rel=1e-2)


@pytest.mark.django_db
def test_drink_months_quantity_sum(drinks):
    actual = Drink.objects.month_sum(1999).values_list('sum', flat=True)

    expect = [2.5, 3.0]

    assert expect == pytest.approx(actual, rel=1e-2)


@pytest.mark.django_db
def test_drink_months_month_num(drinks):
    actual = Drink.objects.month_sum(1999).values_list('month', flat=True)

    expect = [1, 2]

    assert expect == list(actual)


@pytest.mark.django_db
def test_drink_months_month_len(drinks):
    actual = Drink.objects.month_sum(1999).values_list('monthlen', flat=True)

    expect = [31, 28]

    assert expect == list(actual)


@pytest.mark.django_db
@freeze_time('1999-11-01')
def test_drink_days_sum_november():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 11, 1), quantity=1.5)

    actual = Drink.objects.day_sum(1999)

    assert 2.5 == actual['qty']
    assert 4.1 == round(actual['per_day'], 2)


@pytest.mark.django_db
@freeze_time('1999-01-03')
def test_drink_days_sum_january():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 11, 1), quantity=1.5)

    actual = Drink.objects.day_sum(1999)

    assert 1.0 == actual['qty']
    assert 166.67 == round(actual['per_day'], 2)
