from datetime import date, datetime

import pytest
from freezegun import freeze_time

from ..lib.drinks_stats import DrinkStats, std_av


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


@freeze_time('2019-10-10')
def test_std_av():
    actual = std_av(2019, 273.5)

    expect = [
        {'title': 'Std AV', 'total': 683.75, 'per_day': 2.42,
            'per_week': 16.68, 'per_month': 68.38},
        {'title': 'Alus, 0.5L', 'total': 273.5, 'per_day': 0.97,
            'per_week': 6.67, 'per_month': 27.35},
        {'title': 'Vynas, 1L', 'total': 68.38, 'per_day': 0.24,
            'per_week': 1.67, 'per_month': 6.84},
        {'title': 'Degtinė, 1L', 'total': 17.09, 'per_day': 0.06,
            'per_week': 0.42, 'per_month': 1.71},
    ]

    assert 4 == len(actual)

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
        {'title': 'Std AV', 'total': 683.75, 'per_day': 1.87,
            'per_week': 13.15, 'per_month': 56.98},
        {'title': 'Alus, 0.5L', 'total': 273.5, 'per_day': 0.75,
            'per_week': 5.26, 'per_month': 22.79},
        {'title': 'Vynas, 1L', 'total': 68.38, 'per_day': 0.19,
            'per_week': 1.31, 'per_month': 5.70},
        {'title': 'Degtinė, 1L', 'total': 17.09, 'per_day': 0.05,
            'per_week': 0.33, 'per_month': 1.42},
    ]

    assert 4 == len(actual)

    for i, row in enumerate(actual):
        for k, v in row.items():
            if k == 'title':
                assert expect[i][k] == v
            else:
                assert expect[i][k] == round(v, 2)
