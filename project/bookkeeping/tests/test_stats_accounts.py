import pytest

from ..lib.stats_accounts import StatsAccounts
from ...core.tests.utils import _round


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
