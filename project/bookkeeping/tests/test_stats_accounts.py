from decimal import Decimal

import pytest

from ..lib.stats_accounts import StatsAccounts
from ...core.tests.utils import _round
pytestmark = pytest.mark.django_db


def test_past_accounts_balance_empty_current_year(
    _incomes_past, _savings_past, _transactions_past,
    _expenses_past
):
    actual = StatsAccounts(1999).past_accounts_balance

    expect = {
        'Account1': _round(Decimal(4269.85)),
        'Account2': _round(Decimal(1584.85))
    }

    assert expect == actual
