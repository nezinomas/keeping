from datetime import date

import pytest
from django.core.validators import ValidationError

from ..factories import DrinkFactory
from ..models import Drink


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
