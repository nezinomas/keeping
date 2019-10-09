from datetime import date, datetime

import pytest

from ..lib.drinks_stats import DrinkStats


@pytest.fixture
def month_sum():
    return [
        {'date': date(2019, 5, 1), 'sum': 14.0, 'per_month': 100.0,
            'month': 5, 'monthlen': 31},
        {'date': date(2019, 8, 1), 'sum': 47.0, 'per_month': 200.0,
            'month': 8, 'monthlen': 31},
        {'date': date(2019, 10, 1), 'sum': 1.0, 'per_month': 160.0,
            'month': 10, 'monthlen': 31},
    ]


def test_per_month_consumsion(month_sum):
    actual = DrinkStats(month_sum).consumsion

    assert 12 == len(actual)

    assert 0 == actual[0]
    assert 100.0 == actual[4]
    assert 200.0 == actual[7]
    assert 160.0 == actual[9]


def test_per_month_consumsion_empty():
    actual = DrinkStats([]).consumsion

    assert 12 == len(actual)

    assert 0 == actual[0]
    assert 0 == actual[11]


def test_per_month_consumsion_invalid_data01():
    actual = DrinkStats([{'x': 'X'}]).consumsion

    assert 12 == len(actual)

    assert 0 == actual[0]
    assert 0 == actual[11]


def test_per_month_consumsion_invalid_data02():
    actual = DrinkStats([{'month': 12}]).consumsion

    assert 12 == len(actual)

    assert 0 == actual[0]
    assert 0 == actual[11]


def test_per_month_quantity(month_sum):
    actual = DrinkStats(month_sum).quantity

    assert 12 == len(actual)

    assert 0 == actual[0]
    assert 14.0 == actual[4]
    assert 47.0 == actual[7]
    assert 1.0 == actual[9]


def test_per_month_quantity_empty():
    actual = DrinkStats([]).quantity

    assert 12 == len(actual)

    assert 0 == actual[0]
    assert 0 == actual[11]


def test_per_month_quantity_invalid_data():
    actual = DrinkStats([{'x': 'X'}]).quantity

    assert 12 == len(actual)

    assert 0 == actual[0]
    assert 0 == actual[11]
