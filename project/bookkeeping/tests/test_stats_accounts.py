import pytest

from ...core.tests.utils import _round
from ..lib.stats_accounts import StatsAccounts
from . import helper as H


def test_balance(_account_data):
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

    actual = StatsAccounts(1999, _account_data).balance

    assert expect == actual


def test_balance_only_incomes(_account_data):
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
    H.filter_fixture(_account_data, ['account', 'income',])

    actual = StatsAccounts(1999, _account_data).balance

    assert expect == actual


def test_balance_only_expenses(_account_data):
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
    H.filter_fixture(_account_data, ['account', 'expense'])

    actual = StatsAccounts(1999, _account_data).balance

    assert expect == actual


def test_balance_only_transactions(_account_data):
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
    H.filter_fixture(_account_data, ['account', 'transaction'])

    actual = StatsAccounts(1999, _account_data).balance

    assert expect == actual


def test_balance_only_savings(_account_data):
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
    H.filter_fixture(_account_data, ['account', 'saving'])

    actual = StatsAccounts(1999, _account_data).balance

    assert expect == actual


def test_balance_only_savings_close(_account_data):
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
    H.filter_fixture(_account_data, ['account', 'savingclose'])

    actual = StatsAccounts(1999, _account_data).balance

    assert expect == actual


def test_total_past_amount(_account_data):
    expect = 3.75

    actual = StatsAccounts(1999, _account_data).past_amount

    assert expect == actual


def test_total_now_mount(_account_data):
    expect = 3.25

    actual = StatsAccounts(1999, _account_data).current_amount

    assert expect == actual


def test_balance_past(_account_data):
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

    actual = StatsAccounts(1970, _account_data).balance

    assert expect == actual


def test_total_past_amount_past(_account_data):
    expect = 0

    actual = StatsAccounts(1970, _account_data).past_amount

    assert expect == actual


def test_balance_no_data():
    actual = StatsAccounts(1, {}).balance

    assert actual.empty
