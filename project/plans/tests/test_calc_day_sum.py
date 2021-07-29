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
        {'january': Decimal(10.01), 'february': Decimal(10.01),
            'necessary': False, 'title': 'T1'},
        {'january': Decimal(20.02), 'february': Decimal(20.02),
            'necessary': True, 'title': 'T2'},
        {'january': Decimal(30.03), 'february': Decimal(30.03),
            'necessary': False, 'title': 'T3'},
        {'january': Decimal(40.04), 'february': Decimal(40.04),
            'necessary': True, 'title': 'T4'},
    ]

    obj._savings = [
        {'january': Decimal(32.33), 'february': Decimal(32.33)},
        {'january': Decimal(32.33), 'february': Decimal(32.33)},
    ]

    obj._days = [
        {'january': Decimal(25.0), 'february': Decimal(26.0)},
    ]

    obj._necessary = [
        {'january': None, 'february': Decimal(100.0)},
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
    assert 775.32 == round(actual['february'], 2)


def test_expenses_necessary(data):
    actual = CalcDaySum(2020).expenses_necessary

    assert 124.72 == actual['january']
    assert 224.72 == actual['february']


def test_day_calced(data):
    actual = CalcDaySum(2020).day_calced

    assert 25.01 == round(actual['january'], 2)
    assert 26.74 == round(actual['february'], 2)


def test_day_input(data):
    actual = CalcDaySum(2020).day_input

    assert 25.0 == round(actual['january'], 2)
    assert 26.0 == round(actual['february'], 2)


def test_remains(data):
    actual = CalcDaySum(2020).remains

    assert 0.31 == round(actual['january'], 2)
    assert 21.32 == round(actual['february'], 2)


def test_additional_necessary(data):
    actual = CalcDaySum(2020).necessary

    assert 0.0 == round(actual['january'], 2)
    assert 100.0 == round(actual['february'], 2)


def test_plans_stats_list(data):
    actual = CalcDaySum(2020).plans_stats

    assert 4 == len(actual)


def test_plans_stats_expenses_necessary(data):
    actual = CalcDaySum(2020).plans_stats

    assert 'Būtinos išlaidos' == actual[0].type
    assert 124.72 == actual[0].january
    assert 224.72 == actual[0].february


def test_plans_stats_expenses_free(data):
    actual = CalcDaySum(2020).plans_stats
    assert 'Lieka kasdienybei' == actual[1].type
    assert 775.31 == round(actual[1].january, 2)
    assert 775.32 == round(actual[1].february, 2)


def test_plans_stats_day_sum(data):
    actual = CalcDaySum(2020).plans_stats
    assert 'Suma dienai' in actual[2].type
    assert 25.01 == round(actual[2].january, 2)
    assert 26.74 == round(actual[2].february, 2)


def test_plans_stats_remains(data):
    actual = CalcDaySum(2020).plans_stats
    assert 'Likutis' == actual[3].type
    assert 0.31 == round(actual[3].january, 2)
    assert 21.32 == round(actual[3].february, 2)


def test_targets(data):
    obj = CalcDaySum(2020)

    actual = obj.targets(1)

    expect = {'T1': 10.01, 'T2': 20.02, 'T3': 30.03, 'T4': 40.04}

    assert expect == actual


def test_targets_entered_saving_title(data):
    obj = CalcDaySum(2020)

    actual = obj.targets(1, 'X')

    expect = {'T1': 10.01, 'T2': 20.02, 'T3': 30.03, 'T4': 40.04, 'X': 64.66}

    assert expect == actual


def test_target_with_nones(data_empty):
    obj = CalcDaySum(2020)

    obj._data._expenses = [{'january': None, 'necessary': False, 'title': 'T1'}]

    actual = obj.targets(1)

    expect = {'T1': 0.0}

    assert expect == actual
