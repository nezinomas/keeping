from datetime import date
from decimal import Decimal

import pytest

from ..lib.balance_months import BalanceMonths as T


@pytest.fixture()
def _incomes():
    return [
        {'date': date(1999, 1, 1), 'incomes': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'incomes': Decimal(1.25)},
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


def test_balance_months(_incomes, _expenses, _residual, _expect):
    actual = T(_incomes, _expenses, _residual).balance

    assert _expect == actual


def test_balance_months_totals(_incomes, _expenses, _residual):
    expect = {'incomes': 6.75, 'expenses': 1.75, 'balance': 5.0, 'residual': 70.75}
    actual = T(_incomes, _expenses, _residual).totals

    assert expect == actual


def test_balance_months_average(_incomes, _expenses, _residual):
    expect = {'incomes': 3.38, 'expenses': 1.75, 'balance': 2.5, 'residual': 5.90}
    actual = T(_incomes, _expenses, _residual).average

    assert expect == pytest.approx(actual, rel=1e-2)


def test_amount_start():
    actual = T(None, None, 10).amount_start

    assert 10 == actual


def test_amount_start_none():
    actual = T(None, None, None).amount_start

    assert 0.0 == actual


def test_amount_end(_incomes, _expenses, _residual):
    actual = T(_incomes, _expenses, _residual).amount_end

    assert 6.0 == actual


def test_amount_end_none():
    actual = T(None, None, None).amount_end

    assert 0.0 == actual


def test_balance_amount(_incomes, _expenses, _residual):
    actual = T(_incomes, _expenses, _residual).balance_amount

    assert 5.0 == actual


def test_balance_none():
    actual = T([], [], None).balance_amount

    assert 0.0 == actual
