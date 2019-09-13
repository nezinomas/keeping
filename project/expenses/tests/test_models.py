from datetime import date
from decimal import Decimal

import pytest

from ..models import Expense as T

pytestmark = pytest.mark.django_db


def test_sums_months(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'ex': Decimal(0.5)},
        {'date': date(1999, 12, 1), 'ex': Decimal(1.25)},
    ]

    actual = [*T.objects.expense_sum(1999, 'ex')]

    assert expect == actual


def test_expense_type_sum(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'ex': Decimal(0.5), 'title': 'Expense Type'},
        {'date': date(1999, 12, 1), 'ex': Decimal(1.25), 'title': 'Expense Type'},
    ]

    actual = [*T.objects.expense_type_sum(1999, 'ex')]

    assert expect == actual
