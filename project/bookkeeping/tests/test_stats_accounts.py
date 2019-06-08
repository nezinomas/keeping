from decimal import Decimal

import pytest

from ..lib.stats_accounts import StatsAccounts
from ...core.tests.utils import _round
pytestmark = pytest.mark.django_db


def test_past_accounts_balance_empty_current_year(_data):
    actual = StatsAccounts(1999, _data).past_accounts_balance

    expect = {
        'Account1': _round(4019.68),
        'Account2': _round(1119.68)
    }

    assert expect == actual
