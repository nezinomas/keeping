from decimal import Decimal

import pandas as pd
import pytest


from ..lib.balance import Balance as T


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
        {'year': 1970, 'expenses': Decimal('1'), 'id': 2},
        {'year': 1999, 'expenses': Decimal('1'), 'id': 1},
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


@pytest.fixture
def savings():
    return [
        {'year': 1970, 'incomes': Decimal('1'), 'fees': Decimal('0.5'), 'id': 1},
        {'year': 1970, 'incomes': Decimal('3'), 'fees': Decimal('0.5'), 'id': 2},
        {'year': 1999, 'incomes': Decimal('10'), 'fees': Decimal('0.5'), 'id': 1},
        {'year': 1999, 'incomes': Decimal('13'), 'fees': Decimal('0.5'), 'id': 2},
    ]


def test_account_balance_columns(incomes1):
    obj = T().accounts()
    obj.create_balance(data=[incomes1])

    actual = obj._balance.columns

    assert 'past' in actual
    assert 'incomes' in actual
    assert 'expenses' in actual
    assert 'balance' in actual
    assert 'have' in actual
    assert 'delta' in actual
    assert 'account_id' in actual


def test_account_balance_no_data():
    obj = T().accounts()
    actual = obj.balance

    assert actual == []


def test_account_balance_empty_data():
    obj = T().accounts()
    actual = obj.balance

    assert actual == []


def test_account_balance_wrong_data():
    obj = T().accounts()
    obj.create_balance(data=[[{'x':'x'}]])
    actual = obj.balance

    assert actual == []


def test_account_balance_only_incomes(incomes1, incomes2):
    obj = T().accounts()
    obj.create_balance(data=[incomes1, incomes2])
    actual = obj.balance

    # Account1
    assert actual[0]['year'] == 1970
    assert actual[0]['account_id'] == 1
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 2.0
    assert actual[0]['expenses'] == 0.0
    assert actual[0]['balance'] == 2.0
    assert actual[0]['have'] == 0.0
    assert actual[0]['delta'] == -2.0

    assert actual[1]['year'] == 1999
    assert actual[1]['account_id'] == 1
    assert actual[1]['past'] == 2.0
    assert actual[1]['incomes'] == 4.0
    assert actual[1]['expenses'] == 0.0
    assert actual[1]['balance'] == 6.0
    assert actual[1]['have'] == 0.0
    assert actual[1]['delta'] == -6.0

    # Account2
    assert actual[2]['year'] == 1970
    assert actual[2]['account_id'] == 2
    assert actual[2]['past'] == 0.0
    assert actual[2]['incomes'] == 3.0
    assert actual[2]['expenses'] == 0.0
    assert actual[2]['balance'] == 3.0
    assert actual[2]['have'] == 0.0
    assert actual[2]['delta'] == -3.0

    assert actual[3]['year'] == 1999
    assert actual[3]['account_id'] == 2
    assert actual[3]['past'] == 3.0
    assert actual[3]['incomes'] == 5.0
    assert actual[3]['expenses'] == 0.0
    assert actual[3]['balance'] == 8.0
    assert actual[3]['have'] == 0.0
    assert actual[3]['delta'] == -8.0


def test_account_balance_incomes_expenses(incomes1, incomes2, expenses):
    obj = T().accounts()
    obj.create_balance(data=[incomes1, incomes2, expenses, expenses])

    actual = obj.balance

    # Account1
    assert actual[0]['year'] == 1970
    assert actual[0]['account_id'] == 1
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 2.0
    assert actual[0]['expenses'] == 2.0
    assert actual[0]['balance'] == 0.0
    assert actual[0]['have'] == 0.0
    assert actual[0]['delta'] == 0.0

    assert actual[1]['year'] == 1999
    assert actual[1]['account_id'] == 1
    assert actual[1]['past'] == 0.0
    assert actual[1]['incomes'] == 4.0
    assert actual[1]['expenses'] == 2.0
    assert actual[1]['balance'] == 2.0
    assert actual[1]['have'] == 0.0
    assert actual[1]['delta'] == -2.0

    # Account2
    assert actual[2]['year'] == 1970
    assert actual[2]['account_id'] == 2
    assert actual[2]['past'] == 0.0
    assert actual[2]['incomes'] == 3.0
    assert actual[2]['expenses'] == 2.0
    assert actual[2]['balance'] == 1.0
    assert actual[2]['have'] == 0.0
    assert actual[2]['delta'] == -1.0

    assert actual[3]['year'] == 1999
    assert actual[3]['account_id'] == 2
    assert actual[3]['past'] == 1.0
    assert actual[3]['incomes'] == 5.0
    assert actual[3]['expenses'] == 2.0
    assert actual[3]['balance'] == 4.0
    assert actual[3]['have'] == 0.0
    assert actual[3]['delta'] == -4.0


def test_account_balance_incomes_expenses_with_fee(incomes1, incomes2):
    expenses = [
        {'year': 1970, 'expenses': Decimal('1'), 'fees': Decimal('0.25'), 'id': 1},
        {'year': 1970, 'expenses': Decimal('1'), 'fees': Decimal('0.25'),  'id': 2},
        {'year': 1999, 'expenses': Decimal('1'), 'fees': Decimal('0.25'),  'id': 1},
        {'year': 1999, 'expenses': Decimal('1'), 'fees': Decimal('0.25'),  'id': 2},
    ]

    obj = T().accounts()
    obj.create_balance(data=[incomes1, incomes2, expenses, expenses])

    actual = obj.balance

    # assert where is no fee column
    keys = actual[0].keys()
    assert 'fees' not in keys

    # Account1
    assert actual[0]['year'] == 1970
    assert actual[0]['account_id'] == 1
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 2.0
    assert actual[0]['expenses'] == 2.5
    assert actual[0]['balance'] == -0.5
    assert actual[0]['have'] == 0.0
    assert actual[0]['delta'] == 0.5

    assert actual[1]['year'] == 1999
    assert actual[1]['account_id'] == 1
    assert actual[1]['past'] == -0.5
    assert actual[1]['incomes'] == 4.0
    assert actual[1]['expenses'] == 2.5
    assert actual[1]['balance'] == 1.0
    assert actual[1]['have'] == 0.0
    assert actual[1]['delta'] == -1.0

    # Account2
    assert actual[2]['year'] == 1970
    assert actual[2]['account_id'] == 2
    assert actual[2]['past'] == 0.0
    assert actual[2]['incomes'] == 3.0
    assert actual[2]['expenses'] == 2.5
    assert actual[2]['balance'] == 0.5
    assert actual[2]['have'] == 0.0
    assert actual[2]['delta'] == -0.5

    assert actual[3]['year'] == 1999
    assert actual[3]['account_id'] == 2
    assert actual[3]['past'] == 0.5
    assert actual[3]['incomes'] == 5.0
    assert actual[3]['expenses'] == 2.5
    assert actual[3]['balance'] == 3.0
    assert actual[3]['have'] == 0.0
    assert actual[3]['delta'] == -3.0


def test_account_balance_incomes_expenses_have(incomes1, incomes2, expenses, have):
    obj = T().accounts()
    obj.create_balance(data=[incomes1, incomes2, expenses, expenses, have])
    actual = obj.balance

    # Account1
    assert actual[0]['year'] == 1970
    assert actual[0]['account_id'] == 1
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 2.0
    assert actual[0]['expenses'] == 2.0
    assert actual[0]['balance'] == 0.0
    assert actual[0]['have'] == 5.0
    assert actual[0]['delta'] == 5.0

    assert actual[1]['year'] == 1999
    assert actual[1]['account_id'] == 1
    assert actual[1]['past'] == 0.0
    assert actual[1]['incomes'] == 4.0
    assert actual[1]['expenses'] == 2.0
    assert actual[1]['balance'] == 2.0
    assert actual[1]['have'] == 15.0
    assert actual[1]['delta'] == 13.0

    # Account2
    assert actual[2]['year'] == 1970
    assert actual[2]['account_id'] == 2
    assert actual[2]['past'] == 0.0
    assert actual[2]['incomes'] == 3.0
    assert actual[2]['expenses'] == 2.0
    assert actual[2]['balance'] == 1.0
    assert actual[2]['have'] == 10.0
    assert actual[2]['delta'] == 9.0

    assert actual[3]['year'] == 1999
    assert actual[3]['account_id'] == 2
    assert actual[3]['past'] == 1.0
    assert actual[3]['incomes'] == 5.0
    assert actual[3]['expenses'] == 2.0
    assert actual[3]['balance'] == 4.0
    assert actual[3]['have'] == 20.0
    assert actual[3]['delta'] == 16.0


def test_total_row_no_year(incomes1, incomes2, expenses, have):
    obj = T().accounts()
    obj.create_balance(data=[incomes1, incomes2, expenses, expenses, have])
    actual = obj.total_row

    assert actual['past'] == 1.0
    assert actual['incomes'] == 9.0
    assert actual['expenses'] == 4.0
    assert actual['balance'] == 6.0
    assert actual['have'] == 35.0
    assert actual['delta'] == 29.0


def test_total_row_with_year(incomes1, incomes2, expenses, have):
    obj = T().accounts(year=1970)
    obj.create_balance(data=[incomes1, incomes2, expenses, expenses, have])
    actual = obj.total_row

    assert actual['past'] == 0.0
    assert actual['incomes'] == 5.0
    assert actual['expenses'] == 4.0
    assert actual['balance'] == 1.0
    assert actual['have'] == 15.0
    assert actual['delta'] == 14.0


def test_total_row_no_data():
    obj = T().accounts()
    obj.create_balance(data=[])
    actual = obj.total_row

    assert actual == {}


def test_account_balance_start_no_year(incomes1, incomes2, expenses, have):
    obj = T().accounts()
    obj.create_balance(data=[incomes1, incomes2, expenses, expenses, have])
    actual = obj.balance_start

    assert actual == 1.0


def test_account_balance_start_with_year(incomes1, incomes2, expenses, have):
    obj = T().accounts(year=1970)
    obj.create_balance(data=[incomes1, incomes2, expenses, expenses, have])
    actual = obj.balance_start

    assert actual == 0.0


def test_account_balance_end_no_year(incomes1, incomes2, expenses, have):
    obj = T().accounts()
    obj.create_balance(data=[incomes1, incomes2, expenses, expenses, have])
    actual = obj.balance_end

    assert actual == 6.0


def test_account_balance_end_with_year(incomes1, incomes2, expenses, have):
    obj = T().accounts(year=1970)
    obj.create_balance(data=[incomes1, incomes2, expenses, expenses, have])
    actual = obj.balance_end

    assert actual == 1.0


def test_account_balance_year_account_id_link(incomes1):
    obj = T().accounts()
    obj.create_balance(data=[incomes1, [{'id': 3, 'year': 1970, 'x': 4}]])
    actual = obj.year_account_link

    assert actual[1970] == [1, 2, 3]
    assert actual[1999] == [1, 2]


def test_saving_balance_columns(incomes1):
    obj = T().savings()
    obj.create_balance(data=[incomes1])

    actual = obj._balance.columns

    assert 'past_amount' in actual
    assert 'past_fee' in actual
    assert 'fees' in actual
    assert 'invested' in actual
    assert 'incomes' in actual
    assert 'market_value' in actual
    assert 'profit_incomes_proc' in actual
    assert 'profit_incomes_sum' in actual
    assert 'profit_invested_proc' in actual
    assert 'profit_invested_sum' in actual


def test_saving_balance_no_data():
    obj = T().savings()
    actual = obj.balance

    assert actual == []


def test_saving_balance_empty_data():
    obj = T().savings()
    actual = obj.balance

    assert actual == []


def test_saving_balance_wrong_data():
    obj = T().savings()
    obj.create_balance(data=[[{'x': 'x'}]])
    actual = obj.balance

    assert actual == []


def test_saving_balance_only_incomes(savings):
    obj = T().savings()
    obj.create_balance(data=[savings, savings])

    actual = obj.balance

    assert actual[0]['saving_type_id'] == 1
    assert actual[0]['year'] == 1970
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['incomes'] == 2.0
    assert actual[0]['fees'] == 1.0
    assert actual[0]['invested'] == 1.0
    assert actual[0]['market_value'] == 0.0
    assert actual[0]['profit_incomes_proc'] == 0.0
    assert actual[0]['profit_incomes_sum'] == -2.0
    assert actual[0]['profit_invested_proc'] == 0.0
    assert actual[0]['profit_invested_sum'] == -1.0

    assert actual[1]['saving_type_id'] == 1
    assert actual[1]['year'] == 1999
    assert actual[1]['past_amount'] == 2.0
    assert actual[1]['past_fee'] == 1.0
    assert actual[1]['incomes'] == 22.0
    assert actual[1]['fees'] == 2.0
    assert actual[1]['invested'] == 20.0
    assert actual[1]['market_value'] == 0.0
    assert actual[1]['profit_incomes_proc'] == 0.0
    assert actual[1]['profit_incomes_sum'] == -22.0
    assert actual[1]['profit_invested_proc'] == 0.0
    assert actual[1]['profit_invested_sum'] == -20.0

    assert actual[2]['saving_type_id'] == 2
    assert actual[2]['year'] == 1970
    assert actual[2]['past_amount'] == 0.0
    assert actual[2]['past_fee'] == 0.0
    assert actual[2]['incomes'] == 6.0
    assert actual[2]['fees'] == 1.0
    assert actual[2]['invested'] == 5.0
    assert actual[2]['market_value'] == 0.0
    assert actual[2]['profit_incomes_proc'] == 0.0
    assert actual[2]['profit_incomes_sum'] == -6.0
    assert actual[2]['profit_invested_proc'] == 0.0
    assert actual[2]['profit_invested_sum'] == -5.0

    assert actual[3]['saving_type_id'] == 2
    assert actual[3]['year'] == 1999
    assert actual[3]['past_amount'] == 6.0
    assert actual[3]['past_fee'] == 1.0
    assert actual[3]['incomes'] == 32.0
    assert actual[3]['fees'] == 2.0
    assert actual[3]['invested'] == 30.0
    assert actual[3]['market_value'] == 0.0
    assert actual[3]['profit_incomes_proc'] == 0.0
    assert actual[3]['profit_incomes_sum'] == -32.0
    assert actual[3]['profit_invested_proc'] == 0.0
    assert actual[3]['profit_invested_sum'] == -30.0


def test_saving_balance_incomes_expenses(savings):
    expenses = [
        {'year': 1970, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'), 'id': 1},
        {'year': 1970, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'),  'id': 2},
        {'year': 1999, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'),  'id': 1},
        {'year': 1999, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'),  'id': 2},
    ]

    obj = T().savings()
    obj.create_balance(data=[savings, savings, expenses])

    actual = obj.balance

    assert actual[0]['saving_type_id'] == 1
    assert actual[0]['year'] == 1970
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['incomes'] == 1.5
    assert actual[0]['fees'] == 1.25
    assert actual[0]['invested'] == 0.25
    assert actual[0]['market_value'] == 0.0
    assert actual[0]['profit_incomes_sum'] == -1.5
    assert actual[0]['profit_invested_sum'] == -0.25
    assert actual[0]['profit_incomes_proc'] == 0.0
    assert actual[0]['profit_invested_proc'] == 0.0

    assert actual[1]['saving_type_id'] == 1
    assert actual[1]['year'] == 1999
    assert actual[1]['past_amount'] == 1.5
    assert actual[1]['past_fee'] == 1.25
    assert actual[1]['incomes'] == 21.0
    assert actual[1]['fees'] == 2.5
    assert actual[1]['invested'] == 18.5
    assert actual[1]['market_value'] == 0.0
    assert actual[1]['profit_incomes_sum'] == -21.0
    assert actual[1]['profit_invested_sum'] == -18.5
    assert actual[1]['profit_incomes_proc'] == 0.0
    assert actual[1]['profit_invested_proc'] == 0.0

    assert actual[2]['saving_type_id'] == 2
    assert actual[2]['year'] == 1970
    assert actual[2]['past_amount'] == 0.0
    assert actual[2]['past_fee'] == 0.0
    assert actual[2]['incomes'] == 5.5
    assert actual[2]['fees'] == 1.25
    assert actual[2]['invested'] == 4.25
    assert actual[2]['market_value'] == 0.0
    assert actual[2]['profit_incomes_sum'] == -5.5
    assert actual[2]['profit_invested_sum'] == -4.25
    assert actual[2]['profit_incomes_proc'] == 0.0
    assert actual[2]['profit_invested_proc'] == 0.0

    assert actual[3]['saving_type_id'] == 2
    assert actual[3]['year'] == 1999
    assert actual[3]['past_amount'] == 5.5
    assert actual[3]['past_fee'] == 1.25
    assert actual[3]['incomes'] == 31.0
    assert actual[3]['fees'] == 2.5
    assert actual[3]['invested'] == 28.5
    assert actual[3]['market_value'] == 0.0
    assert actual[3]['profit_incomes_sum'] == -31.0
    assert actual[3]['profit_invested_sum'] == -28.5
    assert actual[3]['profit_incomes_proc'] == 0.0
    assert actual[3]['profit_invested_proc'] == 0.0


def test_saving_balance_incomes_expenses_have(savings):
    expenses = [
        {'year': 1970, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'), 'id': 1},
        {'year': 1970, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'),  'id': 2},
        {'year': 1999, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'),  'id': 1},
        {'year': 1999, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'),  'id': 2},
    ]

    have = [
        {'year': 1970, 'have': Decimal('2'), 'id': 1},
        {'year': 1970, 'have': Decimal('6'),  'id': 2},
        {'year': 1999, 'have': Decimal('22'),  'id': 1},
        {'year': 1999, 'have': Decimal('33'),  'id': 2},
    ]

    obj = T().savings()
    obj.create_balance(data=[savings, savings, expenses, have])

    actual = obj.balance

    assert actual[0]['saving_type_id'] == 1
    assert actual[0]['year'] == 1970
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['incomes'] == 1.5
    assert actual[0]['fees'] == 1.25
    assert actual[0]['invested'] == 0.25
    assert actual[0]['market_value'] == 2.0
    assert actual[0]['profit_incomes_sum'] == 0.5
    assert actual[0]['profit_invested_sum'] == 1.75
    assert round(actual[0]['profit_incomes_proc'], 2) == 33.33
    assert round(actual[0]['profit_invested_proc'], 2) == 700.00

    assert actual[1]['saving_type_id'] == 1
    assert actual[1]['year'] == 1999
    assert actual[1]['past_amount'] == 1.5
    assert actual[1]['past_fee'] == 1.25
    assert actual[1]['incomes'] == 21.0
    assert actual[1]['fees'] == 2.5
    assert actual[1]['invested'] == 18.5
    assert actual[1]['market_value'] == 22.0
    assert actual[1]['profit_incomes_sum'] == 1.0
    assert actual[1]['profit_invested_sum'] == 3.5
    assert round(actual[1]['profit_incomes_proc'], 2) == 4.76
    assert round(actual[1]['profit_invested_proc'], 2) == 18.92

    assert actual[2]['saving_type_id'] == 2
    assert actual[2]['year'] == 1970
    assert actual[2]['past_amount'] == 0.0
    assert actual[2]['past_fee'] == 0.0
    assert actual[2]['incomes'] == 5.5
    assert actual[2]['fees'] == 1.25
    assert actual[2]['invested'] == 4.25
    assert actual[2]['market_value'] == 6.0
    assert actual[2]['profit_incomes_sum'] == 0.5
    assert actual[2]['profit_invested_sum'] == 1.75
    assert round(actual[2]['profit_incomes_proc'], 2) == 9.09
    assert round(actual[2]['profit_invested_proc'], 2) == 41.18

    assert actual[3]['saving_type_id'] == 2
    assert actual[3]['year'] == 1999
    assert actual[3]['past_amount'] == 5.5
    assert actual[3]['past_fee'] == 1.25
    assert actual[3]['incomes'] == 31.0
    assert actual[3]['fees'] == 2.5
    assert actual[3]['invested'] == 28.5
    assert actual[3]['market_value'] == 33.0
    assert actual[3]['profit_incomes_sum'] == 2.0
    assert actual[3]['profit_invested_sum'] == 4.5
    assert round(actual[3]['profit_incomes_proc'], 2) == 6.45
    assert round(actual[3]['profit_invested_proc'], 2) == 15.79


def test_saving_total_row(savings):
    expenses = [
        {'year': 1970, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'), 'id': 1},
        {'year': 1970, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'),  'id': 2},
        {'year': 1999, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'),  'id': 1},
        {'year': 1999, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'),  'id': 2},
    ]

    have = [
        {'year': 1970, 'have': Decimal('2'), 'id': 1},
        {'year': 1970, 'have': Decimal('6'),  'id': 2},
        {'year': 1999, 'have': Decimal('22'),  'id': 1},
        {'year': 1999, 'have': Decimal('33'),  'id': 2},
    ]

    obj = T().savings()
    obj.create_balance(data=[savings, savings, expenses, have])

    actual = obj.total_row

    assert actual['past_amount'] == 7.0
    assert actual['past_fee'] == 2.5
    assert actual['incomes'] == 52.0
    assert actual['fees'] == 5.0
    assert actual['invested'] == 47.0
    assert actual['market_value'] == 55
    assert actual['profit_incomes_sum'] == 3.0
    assert actual['profit_invested_sum'] == 8
    assert round(actual['profit_incomes_proc'], 2) == 5.77
    assert round(actual['profit_invested_proc'], 2) == 17.02


def test_saving_invested_cannot_be_negative():
    expenses = [
        {'year': 1970, 'expenses': Decimal('0.5'), 'fees': Decimal('0.25'), 'id': 1},
    ]

    have = [
        {'year': 1970, 'have': Decimal('0.1'), 'id': 1},
    ]

    obj = T().savings()
    obj.create_balance(data=[expenses, have])

    actual = obj.balance

    assert actual[0]['incomes'] == -0.5
    assert actual[0]['fees'] == 0.25
    assert actual[0]['invested'] == 0.0
    assert actual[0]['market_value'] == 0.1
    assert actual[0]['profit_incomes_sum'] == 0.6
    assert actual[0]['profit_invested_sum'] == 0.1
    assert round(actual[0]['profit_incomes_proc'], 2) == -120.0
    assert round(actual[0]['profit_invested_proc'], 2) == 0.0


def test_saving_total_market():
    have = [
        {'year': 1970, 'have': Decimal('2'), 'id': 1},
        {'year': 1970, 'have': Decimal('6'),  'id': 2},
        {'year': 1999, 'have': Decimal('22'),  'id': 1},
        {'year': 1999, 'have': Decimal('33'),  'id': 2},
    ]

    obj = T().savings()
    obj.create_balance(data=[have])

    actual = obj.total_market

    assert actual == 55.0


def test_saving_total_market_year():
    have = [
        {'year': 1970, 'have': Decimal('2'), 'id': 1},
        {'year': 1970, 'have': Decimal('6'),  'id': 2},
        {'year': 1999, 'have': Decimal('22'),  'id': 1},
        {'year': 1999, 'have': Decimal('33'),  'id': 2},
    ]

    obj = T().savings(year=1970)
    obj.create_balance(data=[have])

    actual = obj.total_market

    assert actual == 8.0


def test_savings_total_market_empty_lists():
    obj = T().savings()
    obj.create_balance(data=[])

    actual = obj.total_market

    assert actual == 0.0


def test_savings_total_market_no_data():
    obj = T().savings()
    obj.create_balance(data=None)

    actual = obj.total_market

    assert actual == 0.0

