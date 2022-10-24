from datetime import date

import pytest
from freezegun import freeze_time

from ..lib.drinks_stats import DrinkStats

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'drink_type, stdav, qty, expect',
    [
        ('beer', 2.5, 1, [1, 2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('wine', 8, 1, [1, 2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('vodka', 40, 1, [1, 2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('stdav', 1, 1, [1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ]
)
@freeze_time('1999-12-01')
def test_quantity(drink_type, stdav, qty, expect, get_user):
    get_user.drink_type = drink_type

    data = [
        {'date': date(1999, 1, 1), 'qty': qty, 'stdav': stdav},
        {'date': date(1999, 2, 1), 'qty': qty * 2, 'stdav': stdav * 2},
    ]

    actual = DrinkStats(data).quantity

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('wine', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('vodka', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('stdav', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ]
)
@freeze_time('1999-12-01')
def test_quantity_no_data(drink_type, expect, get_user):
    get_user.drink_type = drink_type

    data = []

    actual = DrinkStats(data).quantity

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, qty, stdav, expect',
    [
        ('beer', 1, 2.5, [16.13, 35.71, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('wine', 1, 8, [24.19, 53.57, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('vodka', 1, 40, [32.23, 71.43, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('stdav', 1, 1, [0.32, 0.71, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ]
)
@freeze_time('1999-12-01')
def test_consumption(drink_type, qty, stdav, expect, get_user):
    get_user.drink_type = drink_type

    data = [
        {'date': date(1999, 1, 1), 'qty': qty, 'stdav': stdav},
        {'date': date(1999, 2, 1), 'qty': qty * 2, 'stdav': stdav * 2},
    ]

    actual = DrinkStats(data).consumption

    assert pytest.approx(actual, 0.01) == expect


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('wine', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('vodka', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ('stdav', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ]
)
@freeze_time('1999-12-01')
def test_consumption_no_data(drink_type, expect, get_user):
    get_user.drink_type = drink_type

    data = []

    actual = DrinkStats(data).consumption

    assert actual == expect
