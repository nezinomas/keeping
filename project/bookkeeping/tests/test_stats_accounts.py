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


def test_total_past_amount(_data):
    actual = StatsAccounts(1999, _data).past_amount
    expect = 5139.36

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
