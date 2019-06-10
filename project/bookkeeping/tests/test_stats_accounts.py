from decimal import Decimal

import pytest

from ..lib.stats_accounts import StatsAccounts
from ...core.tests.utils import _round
pytestmark = pytest.mark.django_db


def test_past_accounts_balance_empty_current_year(_data):
    actual = StatsAccounts(1999, _data).balance

    # expect = {
    #     'Account1': {
    #         'past': 4019.68,
    #         'incomes': 3300,
    #         'expenses': 1081.13,
    #         'balance': 6238.55
    #     },
    #     'Account2': {
    #         'past': 1119.68,
    #         'incomes': 4400,
    #         'expenses': 781.13,
    #         'balance': 4738.55
    #     },
    # }
    expect = {
        'Account1': {
            'past': 4019.68,
        },
        'Account2': {
            'past': 1119.68,
        },
    }
    # assert 0
    assert expect == actual
