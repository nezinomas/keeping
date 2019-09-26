from datetime import date
from decimal import Decimal

import pytest

from ..lib.months_balance import MonthsBalance


@pytest.fixture()
def _incomes():
    return [
        {'date': date(1999, 1, 1), 'incomes': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'incomes': Decimal(1.25)},
    ]


@pytest.fixture()
def _savings():
    return [
        {'date': date(1999, 1, 1), 'savings': Decimal(1.0)},
    ]


@pytest.fixture()
def _savings_close():
    return [
        {'date': date(1999, 1, 1), 'to_account': Decimal(0.5)},
    ]


@pytest.fixture()
def _expenses():
    return [
        {'date': date(1999, 1, 1), 'expenses': Decimal(1.75)},
    ]


@pytest.fixture()
def _residual():
    return Decimal(1)


@pytest.fixture
def _expect():
    return [
        {
            'date': date(1999, 1, 1),
            'incomes': 5.5, 'expenses': 1.75, 'balance': 3.75, 'residual': 4.75},
        {
            'date': date(1999, 2, 1),
            'incomes': 1.25, 'expenses': 0.0, 'balance': 1.25, 'residual': 6.0},
        {
            'date': date(1999, 3, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
        {
            'date': date(1999, 4, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
        {
            'date': date(1999, 5, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
        {
            'date': date(1999, 6, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
        {
            'date': date(1999, 7, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
        {
            'date': date(1999, 8, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
        {
            'date': date(1999, 9, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
        {
            'date': date(1999, 10, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
        {
            'date': date(1999, 11, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
        {
            'date': date(1999, 12, 1),
            'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'residual': 6.0},
    ]


def test_months_balance(_incomes, _expenses, _residual, _expect):
    actual = MonthsBalance(year=1999, incomes=_incomes,
                           expenses=_expenses, amount_start=_residual).balance

    assert _expect == actual


def test_months_balance_totals(_incomes, _expenses, _residual):
    expect = {'incomes': 6.75, 'expenses': 1.75, 'balance': 5.0, 'residual': 70.75}
    actual = MonthsBalance(year=1999, incomes=_incomes,
                           expenses=_expenses, amount_start=_residual).totals

    assert expect == actual


def test_months_balance_average(_incomes, _expenses, _residual):
    expect = {'incomes': 3.38, 'expenses': 1.75, 'balance': 2.5, 'residual': 5.90}
    actual = MonthsBalance(year=1999, incomes=_incomes,
                           expenses=_expenses, amount_start=_residual).average

    assert expect == pytest.approx(actual, rel=1e-2)


def test_amount_start():
    actual = MonthsBalance(year=1999, incomes=None,
                           expenses=None, amount_start=10).amount_start

    assert 10 == actual


def test_amount_start_none():
    actual = MonthsBalance(year=1999, incomes=None,
                           expenses=None, amount_start=None).amount_start

    assert 0.0 == actual


def test_amount_end(_incomes, _expenses, _residual):
    actual = MonthsBalance(year=1999, incomes=_incomes,
                           expenses=_expenses, amount_start=_residual).amount_end

    assert 6.0 == actual


def test_amount_end_none():
    actual = MonthsBalance(year=1999, incomes=None,
                           expenses=None, amount_start=None).amount_end

    assert 0.0 == actual


def test_amount_balance(_incomes, _expenses, _residual):
    actual = MonthsBalance(year=1999, incomes=_incomes,
                           expenses=_expenses, amount_start=_residual).amount_balance

    assert 5.0 == actual


def test_balance_none():
    actual = MonthsBalance(year=1999, incomes=[],
                           expenses=[], amount_start=None).amount_balance

    assert 0.0 == actual


def test_balance_income_data(_incomes):
    expect = [5.5, 1.25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    actual = MonthsBalance(year=1999, incomes=_incomes,
                           expenses=[], amount_start=None).income_data

    assert expect == actual


def test_balance_expense_data(_expenses):
    expect = [1.75, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    actual = MonthsBalance(year=1999, incomes=[],
                           expenses=_expenses, amount_start=None).expense_data

    assert expect == actual


def test_balance_save_data(_incomes, _expenses, _residual):
    expect = [4.75, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6]

    actual = MonthsBalance(year=1999, incomes=_incomes,
                           expenses=_expenses, amount_start=_residual).save_data

    assert expect == actual


def test_avg_incomes(_incomes, _expenses):
    actual = MonthsBalance(year=1999, incomes=_incomes,
                           expenses=_expenses, amount_start=None).avg_incomes

    assert 3.38 == pytest.approx(actual, rel=1e-2)


def test_avg_incomes_none():
    actual = MonthsBalance(year=1999, incomes=None,
                           expenses=None, amount_start=None).avg_incomes

    assert 0.0 == actual


def test_avg_expenses(_incomes, _expenses):
    actual = MonthsBalance(year=1999, incomes=_incomes,
                           expenses=_expenses, amount_start=None).avg_expenses

    assert 1.75 == actual


def test_avg_expenses_none():
    actual = MonthsBalance(year=1999, incomes=None,
                           expenses=None, amount_start=None).avg_expenses

    assert 0.0 == actual


def test_months_balace_with_savings(
        _incomes, _expenses, _residual, _expect, _savings):

    expect = {
        'date': date(1999, 1, 1),
        'incomes': 5.5, 'expenses': 2.75, 'balance': 2.75, 'residual': 3.75
    }

    actual = MonthsBalance(year=1999, incomes=_incomes, expenses=_expenses,
                           savings=_savings, amount_start=_residual).balance

    assert 12 == len(actual)
    assert expect == actual[0]


def test_months_balace_with_savings_february_without_savings(
        _incomes, _expenses, _residual, _expect, _savings):

    expect = {
        'date': date(1999, 2, 1),
        'incomes': 1.25, 'expenses': 0.0, 'balance': 1.25, 'residual': 5.0}

    actual = MonthsBalance(year=1999, incomes=_incomes, expenses=_expenses,
                           savings=_savings, amount_start=_residual).balance

    assert 12 == len(actual)
    assert expect == actual[1]


def test_months_balace_with_savings_close(
        _incomes, _expenses, _residual, _expect, _savings_close):

    expect = {
        'date': date(1999, 1, 1),
        'incomes': 6.0, 'expenses': 1.75, 'balance': 4.25, 'residual': 5.25}

    actual = MonthsBalance(year=1999, incomes=_incomes, expenses=_expenses,
                           savings_close=_savings_close, amount_start=_residual).balance

    assert 12 == len(actual)
    assert expect == actual[0]


def test_months_balace_full(
        _incomes, _expenses, _residual, _expect, _savings, _savings_close):

    expect = {
        'date': date(1999, 1, 1),
        'incomes': 6.0, 'expenses': 2.75, 'balance': 3.25, 'residual': 4.25}

    actual = MonthsBalance(year=1999, incomes=_incomes, expenses=_expenses,
                           savings_close=_savings_close, savings=_savings,
                           amount_start=_residual).balance

    assert 12 == len(actual)
    assert expect == actual[0]
