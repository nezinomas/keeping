import pytest

from ...core.tests.utils import _round
from ..lib.stats_accounts import StatsAccounts


def test_balance(_data):
    actual = StatsAccounts(1999, _data).balance

    expect = {
        'Account1': {
            'past': 4019.68,
            'incomes': 3300.00,
            'expenses': 1081.13,
            'balance': 6238.55,
        },
        'Account2': {
            'past': 1119.68,
            'incomes': 4400.00,
            'expenses': 781.13,
            'balance': 4738.55,
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
    expect = 5139.36

    assert expect == actual


def test_total_now_mount(_data):
    actual = StatsAccounts(1999, _data).current_amount
    expect = 10977.10

    assert expect == actual


def test_balance_past(_data):
    actual = StatsAccounts(1970, _data).balance

    expect = {
        'Account1': {
            'past': 0.0,
            'incomes': 5500.0,
            'expenses': 1480.32,
            'balance': 4019.68,
        },
        'Account2': {
            'past': 0.0,
            'incomes': 2100.0,
            'expenses': 980.32,
            'balance': 1119.68,
        },
    }

    assert expect['Account1'] == pytest.approx(actual['Account1'])
    assert expect['Account2'] == pytest.approx(actual['Account2'])


def test_total_past_amount_past(_data):
    actual = StatsAccounts(1970, _data).past_amount
    expect = 0

    assert expect == actual


def test_balance_no_data():
    actual = StatsAccounts(1, {}).balance

    assert actual.empty
