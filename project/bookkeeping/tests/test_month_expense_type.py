from datetime import date
from decimal import Decimal

import pytest

from ..lib.month_expense_type import MonthExpenseType as T


@pytest.fixture
def _ex():
    return ([
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'T1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(0.25), 'title': 'T2'},
        {'date': date(1999, 1, 2), 'sum': Decimal(0.75), 'title': 'T1'},
    ])


def test_balance_lenght_empty_expenses():
    actual = T(1999, 1, []).balance

    assert 31 == len(actual)


def test_balance_lenght_none_expenses():
    actual = T(1999, 1, None).balance

    assert 31 == len(actual)
