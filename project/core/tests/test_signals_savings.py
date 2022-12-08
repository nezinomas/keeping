from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from ..signals import Savings
import pytest


@pytest.fixture(name="incomes")
def fixture_incomes():
    return [
        # id: 1, year: 2000
        {'year': 2000, 'incomes': Decimal('100'), 'fee': Decimal('2'), 'id': 1},
        {'year': 2000, 'incomes': Decimal('100'), 'fee': Decimal('2'), 'id': 1},
        # id: 1, year: 1999
        {'year': 1999, 'incomes': Decimal('50'), 'fee': Decimal('1'), 'id': 1},
        {'year': 1999, 'incomes': Decimal('50'), 'fee': Decimal('1'), 'id': 1},
        # id: 2, year: 1999
        {'year': 1999, 'incomes': Decimal('55'), 'fee': Decimal('3'), 'id': 2},
        {'year': 1999, 'incomes': Decimal('55'), 'fee': Decimal('3'), 'id': 2},
        # id: 2, year: 2000
        {'year': 2000, 'incomes': Decimal('110'), 'fee': Decimal('4'), 'id': 2},
        {'year': 2000, 'incomes': Decimal('110'), 'fee': Decimal('4'), 'id': 2},
    ]


@pytest.fixture(name="expenses")
def fixture_expenses():
    return [
        # id: 1, year: 2000
        {'year': 2000, 'expenses': Decimal('50'), 'fee': Decimal('2'), 'id': 1},
        {'year': 2000, 'expenses': Decimal('50'), 'fee': Decimal('2'), 'id': 1},
        # id: 1, year: 1999
        {'year': 1999, 'expenses': Decimal('25'), 'fee': Decimal('3'), 'id': 1},
        {'year': 1999, 'expenses': Decimal('25'), 'fee': Decimal('3'), 'id': 1},
        # id: 2, year: 2000
        {'year': 2000, 'expenses': Decimal('55'), 'fee': Decimal('1'), 'id': 2},
        {'year': 2000, 'expenses': Decimal('55'), 'fee': Decimal('1'), 'id': 2},
    ]


@pytest.fixture(name="have")
def fixture_have():
    return [
        {'id': 1, 'year': 1999, 'have': Decimal('75'), 'latest_check': datetime(1999, 1, 1)},
        {'id': 1, 'year': 2000, 'have': Decimal('300'), 'latest_check': datetime(2000, 1, 1)},
        {'id': 2, 'year': 1999, 'have': Decimal('100'), 'latest_check': datetime(1999, 1, 1)},
        {'id': 2, 'year': 2000, 'have': Decimal('250'), 'latest_check': datetime(2000, 1, 1)},
    ]


def test_table(incomes, expenses, have):
    incomes.extend([
        {'year': 1998, 'incomes': Decimal('15'), 'fee': Decimal('1'), 'id': 1},
        {'year': 1997, 'incomes': Decimal('5'), 'fee': Decimal('1'), 'id': 1},
    ])
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=have)
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1997
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['fee'] == 1.0
    assert actual[0]['incomes'] == 5.0
    assert actual[0]['invested'] == 4.0
    assert actual[0]['market_value'] == 0.0
    assert round(actual[0]['profit_incomes_proc'], 2) == -100.0
    assert actual[0]['profit_incomes_sum'] == -5.0
    assert round(actual[0]['profit_invested_proc'], 2) == -100.0
    assert actual[0]['profit_invested_sum'] == -4.0
    assert actual[0]['latest_check'] == 0.0

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 1998
    assert actual[1]['past_amount'] == 5.0
    assert actual[1]['past_fee'] == 1.0
    assert actual[1]['fee'] == 2.0
    assert actual[1]['incomes'] == 20.0
    assert actual[1]['invested'] == 18.0
    assert actual[1]['market_value'] == 0.0
    assert round(actual[1]['profit_incomes_proc'], 2) == -100.0
    assert actual[1]['profit_incomes_sum'] == -20.0
    assert round(actual[1]['profit_invested_proc'], 2) == -100.0
    assert actual[1]['profit_invested_sum'] == -18.0
    assert actual[1]['latest_check'] == 0.0

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 1999
    assert actual[2]['past_amount'] == 20.0
    assert actual[2]['past_fee'] == 2.0
    assert actual[2]['fee'] == 10.0
    assert actual[2]['incomes'] == 70.0
    assert actual[2]['invested'] == 60.0
    assert actual[2]['market_value'] == 75.0
    assert round(actual[2]['profit_incomes_proc'], 2) == 7.14
    assert actual[2]['profit_incomes_sum'] == 5.0
    assert round(actual[2]['profit_invested_proc'], 2) == 25.0
    assert actual[2]['profit_invested_sum'] == 15.0
    assert actual[2]['latest_check'] == datetime(1999, 1, 1)

    assert actual[3]['id'] == 1
    assert actual[3]['year'] == 2000
    assert actual[3]['past_amount'] == 70.0
    assert actual[3]['past_fee'] == 10.0
    assert actual[3]['fee'] == 18.0
    assert actual[3]['incomes'] == 170.0
    assert actual[3]['invested'] == 152.0
    assert actual[3]['market_value'] == 300.0
    assert round(actual[3]['profit_incomes_proc'], 2) == 76.47
    assert actual[3]['profit_incomes_sum'] == 130.0
    assert round(actual[3]['profit_invested_proc'], 2) == 97.37
    assert actual[3]['profit_invested_sum'] == 148.0
    assert actual[3]['latest_check'] == datetime(2000, 1, 1)

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 1999
    assert actual[4]['past_amount'] == 0.0
    assert actual[4]['past_fee'] == 0.0
    assert actual[4]['fee'] == 6.0
    assert actual[4]['incomes'] == 110.0
    assert actual[4]['invested'] == 104.0
    assert actual[4]['market_value'] == 100.0
    assert round(actual[4]['profit_incomes_proc'], 2) == -9.09
    assert actual[4]['profit_incomes_sum'] == -10.0
    assert round(actual[4]['profit_invested_proc'], 2) == -3.85
    assert actual[4]['profit_invested_sum'] == -4.0
    assert actual[4]['latest_check'] == datetime(1999, 1, 1)

    assert actual[5]['id'] == 2
    assert actual[5]['year'] == 2000
    assert actual[5]['past_amount'] == 110.0
    assert actual[5]['past_fee'] == 6.0
    assert actual[5]['fee'] == 16.0
    assert actual[5]['incomes'] == 220.0
    assert actual[5]['invested'] == 204.0
    assert actual[5]['market_value'] == 250.0
    assert round(actual[5]['profit_incomes_proc'], 2) == 13.64
    assert actual[5]['profit_incomes_sum'] == 30.0
    assert round(actual[5]['profit_invested_proc'], 2) == 22.55
    assert actual[5]['profit_invested_sum'] == 46.0
    assert actual[5]['latest_check'] == datetime(2000, 1, 1)
