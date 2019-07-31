import pytest

from ...core.tests.utils import _round
from ..lib.stats_accounts import StatsAccounts


def test_balance(_data):
    actual = StatsAccounts(1999, _data).balance

    expect = {
        'Account1': {
            'past': 5.75,
            'incomes': 6.75,
            'expenses': 8.5,
            'balance': 4.0,
        },
        'Account2': {
            'past': -2.0,
            'incomes': 8.0,
            'expenses': 6.75,
            'balance': -0.75,
        },
    }

    assert expect == actual


def test_balance_only_incomes(_incomes):
    actual = StatsAccounts(1999, _incomes).balance

    expect = {
        'Account1': {
            'past': 5.25,
            'incomes': 3.25,
            'expenses': 0.0,
            'balance': 8.5,
        },
        'Account2': {
            'past': 4.50,
            'incomes': 3.5,
            'expenses': 0.0,
            'balance': 8.0,
        },
    }

    assert expect == actual


def test_balance_only_expenses(_expenses):
    actual = StatsAccounts(1999, _expenses).balance

    expect = {
        'Account1': {
            'past': -2.50,
            'incomes': 0.0,
            'expenses': 0.50,
            'balance': -3.00,
        },
        'Account2': {
            'past': -2.25,
            'incomes': 0.0,
            'expenses': 1.25,
            'balance': -3.5,
        },
    }

    assert expect == actual


def test_balance_only_transactions(_transactions):
    actual = StatsAccounts(1999, _transactions).balance

    expect = {
        'Account1': {
            'past': 4.0,
            'incomes': 3.25,
            'expenses': 4.5,
            'balance': 2.75,
        },
        'Account2': {
            'past': -4.0,
            'incomes': 4.5,
            'expenses': 3.25,
            'balance': -2.75,
        },
    }

    assert expect == actual


def test_balance_only_savings(_savings):
    actual = StatsAccounts(1999, _savings).balance

    expect = {
        'Account1': {
            'past': -1.25,
            'incomes': 0.0,
            'expenses': 3.50,
            'balance': -4.75,
        },
        'Account2': {
            'past': -0.25,
            'incomes': 0.0,
            'expenses': 2.25,
            'balance': -2.50,
        },
    }

    assert expect == actual


def test_balance_only_savings_close(_savings_close):
    actual = StatsAccounts(1999, _savings_close).balance

    expect = {
        'Account1': {
            'past': 0.25,
            'incomes': 0.25,
            'expenses': 0.0,
            'balance': 0.5,
        },
        'Account2': {
            'past': 0.0,
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
        },
    }

    assert expect == actual


def test_total_past_amount(_data):
    actual = StatsAccounts(1999, _data).past_amount
    expect = 3.75

    assert expect == actual


def test_total_now_mount(_data):
    actual = StatsAccounts(1999, _data).current_amount
    expect = 3.25

    assert expect == actual


def test_balance_past(_data):
    actual = StatsAccounts(1970, _data).balance

    expect = {
        'Account1': {
            'past': 0.0,
            'incomes': 10.75,
            'expenses': 5.0,
            'balance': 5.75,
        },
        'Account2': {
            'past': 0.0,
            'incomes': 5.75,
            'expenses': 7.75,
            'balance': -2.0,
        },
    }

    assert expect == actual


def test_total_past_amount_past(_data):
    actual = StatsAccounts(1970, _data).past_amount
    expect = 0

    assert expect == actual


def test_balance_no_data():
    actual = StatsAccounts(1, {}).balance

    assert actual.empty
