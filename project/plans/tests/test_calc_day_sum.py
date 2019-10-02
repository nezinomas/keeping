from decimal import Decimal

import pytest

from ..lib.calc_day_sum import CalcDaySum, CollectData


@pytest.fixture()
def data(monkeypatch):

    monkeypatch.setattr(
        CollectData,
        '__init__',
        lambda x, y: None
    )

    obj = CollectData(2020)  # leap year
    obj._incomes = [
        {'january': Decimal(400.01), 'february': Decimal(500.02)},
        {'january': Decimal(500.02), 'february': Decimal(500.02)},
    ]

    obj._expenses = [
        {'january': Decimal(10.01), 'february': Decimal(10.01), 'necessary': False},
        {'january': Decimal(20.02), 'february': Decimal(20.02), 'necessary': True},
        {'january': Decimal(30.03), 'february': Decimal(30.03), 'necessary': False},
        {'january': Decimal(40.04), 'february': Decimal(40.04), 'necessary': True},
    ]

    obj._savings = [
        {'january': Decimal(32.33), 'february': Decimal(32.33)},
        {'january': Decimal(32.33), 'february': Decimal(32.33)},
    ]

    obj._days = [
        {'january': Decimal(25.0), 'february': Decimal(26.0)},
    ]

    monkeypatch.setattr(
        CalcDaySum,
        '_get_data',
        lambda x: obj
    )


@pytest.fixture()
def data_empty(monkeypatch):

    monkeypatch.setattr(
        CollectData,
        '__init__',
        lambda x, y: None
    )

    obj = CollectData('xxx')

    monkeypatch.setattr(
        CalcDaySum,
        '_get_data',
        lambda x: obj
    )


def test_incomes(data):
    actual = CalcDaySum(2020).incomes

    assert 900.03 == round(actual['january'], 2)
    assert 0.0 == actual['december']


def test_incomes_no_data(data_empty):
    actual = CalcDaySum(2020).incomes

    assert 0.0 == actual['january']
    assert 0.0 == actual['december']


def test_savings(data):
    actual = CalcDaySum(2020).savings

    assert 64.66 == round(actual['january'], 2)
    assert 64.66 == round(actual['february'], 2)


def test_expenses_free(data):
    actual = CalcDaySum(2020).expenses_free

    assert 775.31 == round(actual['january'], 2)
    assert 875.32 == round(actual['february'], 2)


def test_expenses_necessary(data):
    actual = CalcDaySum(2020).expenses_necessary

    assert 124.72 == actual['january']
    assert 124.72 == actual['february']


def test_day_calced(data):
    actual = CalcDaySum(2020).day_calced

    assert 25.01 == round(actual['january'], 2)
    assert 30.18 == round(actual['february'], 2)


def test_day_input(data):
    actual = CalcDaySum(2020).day_input

    assert 25.0 == round(actual['january'], 2)
    assert 26.0 == round(actual['february'], 2)


def test_remains(data):
    actual = CalcDaySum(2020).remains

    assert 0.31 == round(actual['january'], 2)
    assert 121.32 == round(actual['february'], 2)


def test_plans_stats_list(data):
    actual = CalcDaySum(2020).plans_stats

    assert 4 == len(actual)


def test_plans_stats_expenses_necessary(data):
    actual = CalcDaySum(2020).plans_stats

    assert 'Būtinos išlaidos' == actual[0].type
    assert 124.72 == actual[0].january
    assert 124.72 == actual[0].february


def test_plans_stats_expenses_free(data):
    actual = CalcDaySum(2020).plans_stats
    assert 'Lieka kasdienybei' == actual[1].type
    assert 775.31 == round(actual[1].january, 2)
    assert 875.32 == round(actual[1].february, 2)


def test_plans_stats_day_sum(data):
    actual = CalcDaySum(2020).plans_stats
    assert 'Suma dienai' in actual[2].type
    assert 25.01 == round(actual[2].january, 2)
    assert 30.18 == round(actual[2].february, 2)


def test_plans_stats_remains(data):
    actual = CalcDaySum(2020).plans_stats
    assert 'Likutis' == actual[3].type
    assert 0.31 == round(actual[3].january, 2)
    assert 121.32 == round(actual[3].february, 2)
