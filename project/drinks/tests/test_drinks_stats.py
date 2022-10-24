from datetime import date, datetime

import pytest
from freezegun import freeze_time

from ..lib.drinks_stats import DrinkStats, std_av

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


@freeze_time('2019-10-10')
def test_std_av():
    actual = std_av(2019, 273.5)

    expect = [
        {
            'title': 'Alus, 0.5L',
            'total': 273.5,
            'per_day': 0.97,
            'per_week': 6.67,
            'per_month': 27.35
        }, {
            'title': 'Vynas, 0.75L',
            'total': 85.47,
            'per_day': 0.3,
            'per_week': 2.08,
            'per_month': 8.55
        }, {
            'title': 'Degtinė, 1L',
            'total': 17.09,
            'per_day': 0.06,
            'per_week': 0.42,
            'per_month': 1.71
        }, {
            'title': 'Std Av',
            'total': 683.75,
            'per_day': 2.42,
            'per_week': 16.68,
            'per_month': 68.38
        }
    ]

    assert len(actual) == 4

    for i, row in enumerate(actual):
        for k, v in row.items():
            if k == 'title':
                assert expect[i][k] == v
            else:
                assert expect[i][k] == round(v, 2)


@freeze_time('2019-10-10')
def test_std_av_past_recods():
    actual = std_av(1999, 273.5)

    expect = [
        {
            'title': 'Alus, 0.5L',
            'total': 273.5,
            'per_day': 0.75,
            'per_week': 5.26,
            'per_month': 22.79
        }, {
            'title': 'Vynas, 0.75L',
            'total': 85.47,
            'per_day': 0.23,
            'per_week': 1.64,
            'per_month': 7.12
        }, {
            'title': 'Degtinė, 1L',
            'total': 17.09,
            'per_day': 0.05,
            'per_week': 0.33,
            'per_month': 1.42
        }, {
            'title': 'Std Av',
            'total': 683.75,
            'per_day': 1.87,
            'per_week': 13.15,
            'per_month': 56.98
        }
    ]

    assert len(actual) == 4

    for i, row in enumerate(actual):
        for k, v in row.items():
            if k == 'title':
                assert expect[i][k] == v
            else:
                assert expect[i][k] == round(v, 2)
