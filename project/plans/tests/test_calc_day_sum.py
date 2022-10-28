from decimal import Decimal

import pytest

from ..lib.calc_day_sum import PlanCalculateDaySum, PlanCollectData


@pytest.fixture()
def data():
    obj = type('PlanCollectData', (object,), {})

    obj.year = 2020
    obj.incomes = [
        {'january': Decimal(400.01), 'february': Decimal(500.02)},
        {'january': Decimal(500.02), 'february': Decimal(500.02)},
    ]
    obj.expenses = [
        {
            'january': Decimal(10.01),
            'february': Decimal(10.01),
            'necessary': False,
            'title': 'T1'
        }, {
            'january': Decimal(20.02),
            'february': Decimal(20.02),
            'necessary': True,
            'title': 'T2'
        }, {
            'january': Decimal(30.03),
            'february': Decimal(30.03),
            'necessary': False,
            'title': 'T3'
        }, {
            'january': Decimal(40.04),
            'february': Decimal(40.04),
            'necessary': True,
            'title': 'T4'
        }
    ]

    obj.savings = [
        {'january': Decimal(32.33), 'february': Decimal(32.33)},
        {'january': Decimal(32.33), 'february': Decimal(32.33)},
    ]

    obj.days = [
        {'january': Decimal(25.0), 'february': Decimal(26.0)},
    ]

    obj.necessary = [
        {'january': None, 'february': Decimal(100.0)},
    ]

    return obj


@pytest.fixture()
def data_empty():
    return type('PlanCollectData', (object,), {
        'year': 2020,
        'incomes': [],
        'expenses': [],
        'savings': [],
        'days': [],
        'necessary': [],})


def test_year(data_empty):
    actual = PlanCalculateDaySum(data_empty).year

    assert actual == 2020


def test_incomes(data):
    actual = PlanCalculateDaySum(data).incomes

    assert round(actual['january'], 2) == 900.03
    assert actual['december'] == 0.0


def test_incomes_no_data(data_empty):
    actual = PlanCalculateDaySum(data_empty).incomes

    assert actual['january'] == 0.0
    assert actual['december'] == 0.0


def test_savings(data):
    actual = PlanCalculateDaySum(data).savings

    assert round(actual['january'], 2) == 64.66
    assert round(actual['february'], 2) == 64.66


def test_expenses_free(data):
    actual = PlanCalculateDaySum(data).expenses_free

    assert round(actual['january'], 2) == 775.31
    assert round(actual['february'], 2) == 775.32


def test_expenses_necessary(data):
    actual = PlanCalculateDaySum(data).expenses_necessary

    assert actual['january'] == 124.72
    assert actual['february'] == 224.72


def test_day_calced(data):
    actual = PlanCalculateDaySum(data).day_calced

    assert round(actual['january'], 2) == 25.01
    assert round(actual['february'], 2) == 26.74


def test_day_input(data):
    actual = PlanCalculateDaySum(data).day_input

    assert round(actual['january'], 2) == 25.0
    assert round(actual['february'], 2) == 26.0


def test_remains(data):
    actual = PlanCalculateDaySum(data).remains

    assert round(actual['january'], 2) == 0.31
    assert round(actual['february'], 2) == 21.32


def test_additional_necessary(data):
    actual = PlanCalculateDaySum(data).necessary

    assert round(actual['january'], 2) == 0.0
    assert round(actual['february'], 2) == 100.0


def test_plans_stats_list(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert len(actual) == 4


def test_plans_stats_expenses_necessary(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert 'Būtinos išlaidos' == actual[0].type
    assert actual[0].january == 124.72
    assert actual[0].february == 224.72


def test_plans_stats_expenses_free(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[1].type == 'Lieka kasdienybei'
    assert round(actual[1].january, 2) == 775.31
    assert round(actual[1].february, 2) == 775.32


def test_plans_stats_day_sum(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert 'Suma dienai' in actual[2].type
    assert round(actual[2].january, 2) == 25.01
    assert round(actual[2].february, 2) == 26.74


def test_plans_stats_remains(data):
    actual = PlanCalculateDaySum(data).plans_stats

    assert actual[3].type == 'Likutis'
    assert round(actual[3].january, 2) == 0.31
    assert round(actual[3].february, 2) == 21.32


def test_targets(data):
    obj = PlanCalculateDaySum(data)

    actual = obj.targets(1)

    expect = {'T1': 10.01, 'T2': 20.02, 'T3': 30.03, 'T4': 40.04}

    assert actual == expect


def test_target_with_nones(data_empty):
    data_empty.expenses = [{'january': None, 'necessary': False, 'title': 'T1'}]

    obj = PlanCalculateDaySum(data_empty)

    actual = obj.targets(1)

    expect = {'T1': 0.0}

    assert actual == expect
