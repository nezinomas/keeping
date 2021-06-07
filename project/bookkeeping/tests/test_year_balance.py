from datetime import date
from decimal import Decimal

import pytest
from pandas import Timestamp as pdTime

from ..lib.year_balance import YearBalance


@pytest.fixture()
def _incomes():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'sum': Decimal(1.25)},
    ]


@pytest.fixture()
def _savings():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal(1.0)},
    ]


@pytest.fixture()
def _savings_close():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5)},
    ]


@pytest.fixture()
def _expenses():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal(1.75)},
    ]


@pytest.fixture()
def _money_flow():
    return Decimal(1)


@pytest.fixture
def _expect():
    return [
        {
            'date': pdTime(date(1999, 1, 1)),
            'incomes': 5.5,
            'expenses': 1.75,
            'balance': 3.75,
            'savings': 1.0,
            'savings_close': 0.5,
            'money_flow': 4.25
        }, {
            'date': pdTime(date(1999, 2, 1)),
            'incomes': 1.25,
            'expenses': 0.0,
            'balance': 1.25,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 3, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 4, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 5, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 6, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 7, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 8, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 9, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 10, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 11, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }, {
            'date': pdTime(date(1999, 12, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'money_flow': 5.5
        }
    ]


def test_months_balance(_incomes, _expenses, _savings, _savings_close, _money_flow, _expect):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        savings=_savings,
        savings_close=_savings_close,
        amount_start=_money_flow
    ).balance

    assert actual == _expect


def test_months_balance_no_savings(_incomes, _expenses, _savings_close, _money_flow, _expect):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        savings_close=_savings_close,
        amount_start=_money_flow
    ).balance

    for x in _expect:
        x['savings'] = 0.0
        x['money_flow'] += 1.0

    assert actual == _expect


def test_months_balance_no_savings_close(_incomes, _expenses, _savings, _money_flow, _expect):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        savings=_savings,
        amount_start=_money_flow
    ).balance

    for x in _expect:
        x['savings_close'] = 0.0
        x['money_flow'] -= 1.0
        x['money_flow'] += 0.5

    assert actual == _expect


def test_months_balance_total_row(_incomes, _expenses, _savings, _savings_close, _money_flow, _expect):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        savings=_savings,
        savings_close=_savings_close,
        amount_start=_money_flow
    ).total_row

    expect = {
        'incomes': 6.75,
        'expenses': 1.75,
        'balance': 5.0,
        'savings': 1.0,
        'savings_close': 0.5,
        'money_flow': 64.75
    }

    assert actual == expect


def test_months_balance_average(_incomes, _expenses, _savings, _savings_close, _money_flow, _expect):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        savings=_savings,
        savings_close=_savings_close,
        amount_start=_money_flow
    ).average

    expect = {
        'incomes': 3.38,
        'expenses': 1.75,
        'balance': 2.5,
        'savings': 1.0,
        'savings_close': 0.5,
        'money_flow': 5.39
    }

    assert expect == pytest.approx(actual, rel=1e-2)


def test_amount_start():
    actual = YearBalance(
        year=1999,
        incomes=None,
        expenses=None,
        amount_start=10
    ).amount_start

    assert actual == 10


def test_amount_start_none():
    actual = YearBalance(
        year=1999,
        incomes=None,
        expenses=None,
        amount_start=None
    ).amount_start

    assert actual == 0.0


def test_amount_end(_incomes, _expenses, _savings, _savings_close, _money_flow):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        savings=_savings,
        savings_close=_savings_close,
        amount_start=_money_flow
    ).amount_end

    assert actual == 5.5


def test_amount_end_none():
    actual = YearBalance(
        year=1999,
        incomes=None,
        expenses=None,
        amount_start=None
    ).amount_end

    assert actual == 0.0


def test_amount_balance(_incomes, _expenses, _money_flow):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        amount_start=_money_flow
    ).amount_balance

    assert actual == 5.0


def test_balance_none():
    actual = YearBalance(
        year=1999,
        incomes=[],
        expenses=[],
        amount_start=None
    ).amount_balance

    assert actual == 0.0


def test_balance_income_data(_incomes, _expect):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=[],
        amount_start=None
    ).income_data

    expect = [x['incomes'] for x in _expect]

    assert actual == expect


def test_balance_expense_data(_expenses, _expect):
    actual = YearBalance(
        year=1999,
        incomes=[],
        expenses=_expenses,
        amount_start=None
    ).expense_data

    expect = [x['expenses'] for x in _expect]

    assert actual == expect


def test_balance_money_flow(_incomes, _expenses, _savings, _savings_close, _money_flow, _expect):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        savings=_savings,
        savings_close=_savings_close,
        amount_start=_money_flow
    ).money_flow

    expect = [x['money_flow'] for x in _expect]

    assert actual == expect


def test_avg_incomes(_incomes, _expenses):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        amount_start=None
    ).avg_incomes

    assert pytest.approx(actual, rel=1e-2) == 3.38


def test_avg_incomes_none():
    actual = YearBalance(
        year=1999,
        incomes=None,
        expenses=None,
        amount_start=None
    ).avg_incomes

    assert actual == 0.0


def test_avg_expenses(_incomes, _expenses):
    actual = YearBalance(
        year=1999,
        incomes=_incomes,
        expenses=_expenses,
        amount_start=None
    ).avg_expenses

    assert actual == 1.75


def test_avg_expenses_none():
    actual = YearBalance(
        year=1999,
        incomes=None,
        expenses=None,
        amount_start=None
    ).avg_expenses

    assert actual == 0.0
