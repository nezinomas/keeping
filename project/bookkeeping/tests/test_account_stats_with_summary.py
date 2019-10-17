from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...incomes.factories import IncomeFactory
from ...incomes.models import Income
from ..lib.account_stats import AccountStats
from ..lib.summary import collect_summary_data

pytestmark = pytest.mark.django_db


def test_account_stats_for_two_years_in_past():
    IncomeFactory(date=date(1974, 1, 1), price=5)
    IncomeFactory(date=date(1974, 1, 1), price=5)
    IncomeFactory(date=date(1999, 1, 1), price=2.5)
    IncomeFactory(date=date(1999, 1, 1), price=2.5)
    IncomeFactory(date=date(2000, 1, 1), price=5)

    expect = [{
        'title': 'Account1',
        'past': 15.0,
        'incomes': 5.0,
        'expenses': 0.0,
        'balance': 20.0,
    }]

    summary, _ = collect_summary_data(2000, [Income])
    actual = AccountStats(summary, pd.DataFrame()).balance

    assert_(expect, actual)
