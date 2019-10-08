import pytest

from ..factories import DrinkFactory
from ..models import Drink
from django.core.validators import ValidationError


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
