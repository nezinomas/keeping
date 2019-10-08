from datetime import date

import pytest
from django.core.validators import ValidationError

from ..factories import DrinkFactory, DrinkTargetFactory
from ..models import Drink, DrinkTarget


def test_drink_str():
    actual = DrinkFactory.build()

    assert '1999-01-01: 1' == str(actual)


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
def test_drink_months_sum():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 2, 1), quantity=2.0)
    DrinkFactory(date=date(1999, 2, 1), quantity=1.0)

    actual = list(Drink.objects.month_sum(1999))

    expect = [
        {'date': date(1999, 1, 1), 'sum': 2.5},
        {'date': date(1999, 2, 1), 'sum': 3.0},
    ]

    assert expect == actual


@pytest.mark.django_db
def test_drink_months_sum():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5)

    actual = list(Drink.objects.month_sum(1999, 1))

    expect = [
        {'date': date(1999, 1, 1), 'sum': 2.5},
    ]

    assert expect == actual
