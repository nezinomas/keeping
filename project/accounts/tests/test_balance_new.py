from decimal import Decimal

import pandas as pd
import pytest


from ..lib.balance_new import BalanceNew as T


@pytest.fixture()
def incomes1():
    return [
        {'year': 1970, 'incomes': Decimal('1'), 'id': 1},
        {'year': 1970, 'incomes': Decimal('2'), 'id': 2},
        {'year': 1999, 'incomes': Decimal('3'), 'id': 1},
        {'year': 1999, 'incomes': Decimal('4'), 'id': 2},
    ]


@pytest.fixture
def incomes2():
    return [
        {'year': 1970, 'incomes': Decimal('1'), 'id': 1},
        {'year': 1970, 'incomes': Decimal('1'), 'id': 2},
        {'year': 1999, 'incomes': Decimal('1'), 'id': 1},
        {'year': 1999, 'incomes': Decimal('1'), 'id': 2},
    ]


@pytest.fixture()
def expenses():
    return [
        {'year': 1970, 'expenses': Decimal('1'), 'id': 1},
        {'year': 1999, 'expenses': Decimal('1'), 'id': 1},
        {'year': 1970, 'expenses': Decimal('1'), 'id': 2},
        {'year': 1999, 'expenses': Decimal('1'), 'id': 2},
    ]


@pytest.fixture()
def have():
    return [
        {'year': 1970, 'have': Decimal('5'), 'id': 1},
        {'year': 1999, 'have': Decimal('15'), 'id': 1},
        {'year': 1970, 'have': Decimal('10'), 'id': 2},
        {'year': 1999, 'have': Decimal('20'), 'id': 2},
    ]


def test_balance_no_data():
    actual = T().balance

    assert actual == []


def test_balance_empty_data():
    actual = T(data=[]).balance

    assert actual == []


def test_balance_wrong_data():
    actual = T(data=[[{'x':'x'}]]).balance

    assert actual == []


def test_balance_only_incomes(incomes1, incomes2):
    actual = T(data=[incomes1, incomes2]).balance

    # Account1
    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 2.0
    assert actual[0]['expenses'] == 0.0
    assert actual[0]['balance'] == 2.0
    assert actual[0]['have'] == 0.0
    assert actual[0]['delta'] == -2.0

    assert actual[1]['year'] == 1999
    assert actual[1]['id'] == 1
    assert actual[1]['past'] == 2.0
    assert actual[1]['incomes'] == 4.0
    assert actual[1]['expenses'] == 0.0
    assert actual[1]['balance'] == 6.0
    assert actual[1]['have'] == 0.0
    assert actual[1]['delta'] == -6.0

    # Account2
    assert actual[2]['year'] == 1970
    assert actual[2]['id'] == 2
    assert actual[2]['past'] == 0.0
    assert actual[2]['incomes'] == 3.0
    assert actual[2]['expenses'] == 0.0
    assert actual[2]['balance'] == 3.0
    assert actual[2]['have'] == 0.0
    assert actual[2]['delta'] == -3.0

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['past'] == 3.0
    assert actual[3]['incomes'] == 5.0
    assert actual[3]['expenses'] == 0.0
    assert actual[3]['balance'] == 8.0
    assert actual[3]['have'] == 0.0
    assert actual[3]['delta'] == -8.0


def test_balance_incomes_expenses(incomes1, incomes2, expenses):
    actual = T(data=[incomes1, incomes2, expenses, expenses]).balance

    # Account1
    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 2.0
    assert actual[0]['expenses'] == 2.0
    assert actual[0]['balance'] == 0.0
    assert actual[0]['have'] == 0.0
    assert actual[0]['delta'] == 0.0

    assert actual[1]['year'] == 1999
    assert actual[1]['id'] == 1
    assert actual[1]['past'] == 0.0
    assert actual[1]['incomes'] == 4.0
    assert actual[1]['expenses'] == 2.0
    assert actual[1]['balance'] == 2.0
    assert actual[1]['have'] == 0.0
    assert actual[1]['delta'] == -2.0

    # Account2
    assert actual[2]['year'] == 1970
    assert actual[2]['id'] == 2
    assert actual[2]['past'] == 0.0
    assert actual[2]['incomes'] == 3.0
    assert actual[2]['expenses'] == 2.0
    assert actual[2]['balance'] == 1.0
    assert actual[2]['have'] == 0.0
    assert actual[2]['delta'] == -1.0

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['past'] == 1.0
    assert actual[3]['incomes'] == 5.0
    assert actual[3]['expenses'] == 2.0
    assert actual[3]['balance'] == 4.0
    assert actual[3]['have'] == 0.0
    assert actual[3]['delta'] == -4.0


def test_balance_incomes_expenses_have(incomes1, incomes2, expenses, have):
    actual = T(data=[incomes1, incomes2, expenses, expenses, have]).balance

    # Account1
    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 2.0
    assert actual[0]['expenses'] == 2.0
    assert actual[0]['balance'] == 0.0
    assert actual[0]['have'] == 5.0
    assert actual[0]['delta'] == 5.0

    assert actual[1]['year'] == 1999
    assert actual[1]['id'] == 1
    assert actual[1]['past'] == 0.0
    assert actual[1]['incomes'] == 4.0
    assert actual[1]['expenses'] == 2.0
    assert actual[1]['balance'] == 2.0
    assert actual[1]['have'] == 15.0
    assert actual[1]['delta'] == 13.0

    # Account2
    assert actual[2]['year'] == 1970
    assert actual[2]['id'] == 2
    assert actual[2]['past'] == 0.0
    assert actual[2]['incomes'] == 3.0
    assert actual[2]['expenses'] == 2.0
    assert actual[2]['balance'] == 1.0
    assert actual[2]['have'] == 10.0
    assert actual[2]['delta'] == 9.0

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['past'] == 1.0
    assert actual[3]['incomes'] == 5.0
    assert actual[3]['expenses'] == 2.0
    assert actual[3]['balance'] == 4.0
    assert actual[3]['have'] == 20.0
    assert actual[3]['delta'] == 16.0


def test_total_row_no_year(incomes1, incomes2, expenses, have):
    actual = T(data=[incomes1, incomes2, expenses, expenses, have]).total_row

    assert actual['past'] == 1.0
    assert actual['incomes'] == 9.0
    assert actual['expenses'] == 4.0
    assert actual['balance'] == 6.0
    assert actual['have'] == 35.0
    assert actual['delta'] == 29.0


def test_total_row_with_year(incomes1, incomes2, expenses, have):
    actual = T(year=1970, data=[incomes1, incomes2, expenses, expenses, have]).total_row

    assert actual['past'] == 0.0
    assert actual['incomes'] == 5.0
    assert actual['expenses'] == 4.0
    assert actual['balance'] == 1.0
    assert actual['have'] == 15.0
    assert actual['delta'] == 14.0


def test_total_row_no_data():
    actual = T(data=[]).total_row

    assert actual == {}


def test_balance_start_no_year(incomes1, incomes2, expenses, have):
    actual = T(data=[incomes1, incomes2, expenses, expenses, have]).balance_start

    assert actual == 1.0


def test_balance_start_with_year(incomes1, incomes2, expenses, have):
    actual = T(year=1970, data=[incomes1, incomes2, expenses, expenses, have]).balance_start

    assert actual == 0.0


def test_balance_end_no_year(incomes1, incomes2, expenses, have):
    actual = T(data=[incomes1, incomes2, expenses, expenses, have]).balance_end

    assert actual == 6.0


def test_balance_end_with_year(incomes1, incomes2, expenses, have):
    actual = T(year=1970, data=[incomes1, incomes2, expenses, expenses, have]).balance_end

    assert actual == 1.0
